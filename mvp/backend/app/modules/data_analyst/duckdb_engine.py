"""
DuckDB Engine - Fast in-memory SQL analytics for datasets.

Replaces pandas for data analysis:
- 100x faster on large CSV files
- SQL queries (LLMs generate better SQL than pandas code)
- In-memory, zero server setup
- Auto-profiling with ydata-profiling
- Parquet/JSON/URL ingestion, SUMMARIZE, advanced stats, window functions
- PIVOT/UNPIVOT, COPY TO export, httpfs remote datasets

Falls back gracefully to the existing pandas/CSV parser if not installed.
"""

import io
import os
import tempfile
from typing import Optional

import structlog

logger = structlog.get_logger()

HAS_DUCKDB = False
try:
    import duckdb as _duckdb  # noqa: F401
    HAS_DUCKDB = True
except ImportError:
    pass


def is_duckdb_available() -> bool:
    """Check if duckdb is installed."""
    try:
        import duckdb  # noqa: F401
        return True
    except ImportError:
        return False


def is_profiling_available() -> bool:
    """Check if ydata-profiling is installed."""
    try:
        from ydata_profiling import ProfileReport  # noqa: F401
        return True
    except ImportError:
        return False


def parse_csv_duckdb(content: bytes) -> dict:
    """Parse CSV using DuckDB (100x faster than pandas on large files).

    Returns same format as DataAnalystService._parse_csv() for compatibility.
    """
    if not is_duckdb_available():
        return {}

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")

        # Load CSV into DuckDB
        conn.execute("CREATE TABLE data AS SELECT * FROM read_csv_auto(?)", [io.StringIO(text)])

        # Get column info
        columns_info = conn.execute("DESCRIBE data").fetchall()
        row_count = conn.execute("SELECT COUNT(*) FROM data").fetchone()[0]

        columns = []
        stats = {}

        for col_name, col_type, *_ in columns_info:
            # Get sample values
            sample = conn.execute(f'SELECT DISTINCT "{col_name}" FROM data LIMIT 5').fetchall()
            sample_values = [str(row[0]) for row in sample if row[0] is not None]

            # Count non-null and unique
            non_null = conn.execute(f'SELECT COUNT("{col_name}") FROM data WHERE "{col_name}" IS NOT NULL').fetchone()[0]
            unique = conn.execute(f'SELECT COUNT(DISTINCT "{col_name}") FROM data').fetchone()[0]

            dtype = "numeric" if col_type in ("INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT") else "text"

            columns.append({
                "name": col_name,
                "dtype": dtype,
                "duckdb_type": col_type,
                "non_null": non_null,
                "unique": unique,
                "sample_values": sample_values,
            })

            # Compute stats for numeric columns
            if dtype == "numeric":
                try:
                    stat_row = conn.execute(f'''
                        SELECT
                            MIN("{col_name}") as min_val,
                            MAX("{col_name}") as max_val,
                            AVG("{col_name}") as avg_val,
                            COUNT("{col_name}") as cnt,
                            STDDEV("{col_name}") as std_val,
                            MEDIAN("{col_name}") as median_val
                        FROM data
                        WHERE "{col_name}" IS NOT NULL
                    ''').fetchone()
                    stats[col_name] = {
                        "min": float(stat_row[0]) if stat_row[0] is not None else None,
                        "max": float(stat_row[1]) if stat_row[1] is not None else None,
                        "mean": round(float(stat_row[2]), 4) if stat_row[2] is not None else None,
                        "count": int(stat_row[3]),
                        "std": round(float(stat_row[4]), 4) if stat_row[4] is not None else None,
                        "median": float(stat_row[5]) if stat_row[5] is not None else None,
                    }
                except Exception:
                    pass

        # Preview (first 10 rows as dicts)
        preview_rows = conn.execute("SELECT * FROM data LIMIT 10").fetchall()
        col_names = [c["name"] for c in columns]
        preview = [dict(zip(col_names, [str(v) if v is not None else "" for v in row])) for row in preview_rows]

        conn.close()

        logger.info("duckdb_csv_parsed", rows=row_count, columns=len(columns))

        return {
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "preview": preview,
            "stats": stats,
            "engine": "duckdb",
        }

    except Exception as e:
        logger.warning("duckdb_parse_failed", error=str(e))
        return {}


def query_dataset(content: bytes, sql_query: str) -> dict:
    """Execute a SQL query on a CSV dataset using DuckDB.

    Args:
        content: Raw CSV bytes
        sql_query: SQL query (use 'data' as table name)

    Returns:
        dict with columns, rows, row_count
    """
    if not is_duckdb_available():
        return {"error": "DuckDB not installed", "rows": [], "columns": []}

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE data AS SELECT * FROM read_csv_auto(?)", [io.StringIO(text)])

        result = conn.execute(sql_query)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()

        conn.close()

        return {
            "columns": columns,
            "rows": [dict(zip(columns, [str(v) if v is not None else "" for v in row])) for row in rows[:1000]],
            "row_count": len(rows),
        }

    except Exception as e:
        return {"error": str(e), "rows": [], "columns": []}


def auto_profile(content: bytes, filename: str = "dataset") -> Optional[dict]:
    """Generate automatic profiling report using ydata-profiling.

    Returns a summary dict with key statistics and insights.
    Returns None if ydata-profiling is not installed.
    """
    if not is_profiling_available():
        return None

    try:
        import pandas as pd
        from ydata_profiling import ProfileReport

        text = content.decode("utf-8", errors="replace")
        df = pd.read_csv(io.StringIO(text))

        # Generate minimal profile (fast)
        profile = ProfileReport(df, title=filename, minimal=True, explorative=False)
        desc = profile.get_description()

        # Extract key stats
        summary = {
            "row_count": int(desc.table.get("n", 0)) if hasattr(desc, "table") else len(df),
            "column_count": len(df.columns),
            "missing_cells": int(desc.table.get("n_cells_missing", 0)) if hasattr(desc, "table") else 0,
            "duplicate_rows": int(desc.table.get("n_duplicates", 0)) if hasattr(desc, "table") else 0,
            "memory_size": int(desc.table.get("memory_size", 0)) if hasattr(desc, "table") else 0,
            "columns": {},
        }

        # Per-column stats
        for col in df.columns:
            col_stats = {
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].count()),
                "unique": int(df[col].nunique()),
                "missing_pct": round(df[col].isna().mean() * 100, 1),
            }
            if df[col].dtype in ("int64", "float64"):
                col_stats.update({
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": round(float(df[col].mean()), 4) if not df[col].isna().all() else None,
                    "std": round(float(df[col].std()), 4) if not df[col].isna().all() else None,
                })
            summary["columns"][col] = col_stats

        logger.info("ydata_profiling_complete", columns=len(df.columns), rows=len(df))
        return summary

    except Exception as e:
        logger.warning("ydata_profiling_failed", error=str(e))
        return None


# ---------------------------------------------------------------------------
# Feature 1: Parquet & JSON loaders
# ---------------------------------------------------------------------------

def load_parquet(file_path: str) -> dict:
    """Load a Parquet file into DuckDB and return parsed metadata + preview.

    Args:
        file_path: Absolute path to a .parquet file on disk.

    Returns:
        dict with row_count, column_count, columns, preview, stats, engine.
        Empty dict on failure.
    """
    if not HAS_DUCKDB:
        return {}

    import duckdb

    try:
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_parquet(?)", [file_path]
        )
        result = _extract_table_metadata(conn, "data")
        conn.close()
        logger.info("duckdb_parquet_loaded", file=file_path, rows=result.get("row_count"))
        return result

    except Exception as e:
        logger.warning("duckdb_parquet_failed", error=str(e), file=file_path)
        return {}


def load_json(file_path: str) -> dict:
    """Load a JSON file into DuckDB using read_json_auto and return parsed metadata + preview.

    Args:
        file_path: Absolute path to a .json or .jsonl file on disk.

    Returns:
        dict with row_count, column_count, columns, preview, stats, engine.
        Empty dict on failure.
    """
    if not HAS_DUCKDB:
        return {}

    import duckdb

    try:
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_json_auto(?)", [file_path]
        )
        result = _extract_table_metadata(conn, "data")
        conn.close()
        logger.info("duckdb_json_loaded", file=file_path, rows=result.get("row_count"))
        return result

    except Exception as e:
        logger.warning("duckdb_json_failed", error=str(e), file=file_path)
        return {}


# ---------------------------------------------------------------------------
# Feature 2: Advanced statistical functions
# ---------------------------------------------------------------------------

def compute_advanced_stats(table_name: str, content: bytes) -> dict:
    """Compute advanced statistics on a CSV dataset.

    Runs CORR() for correlation matrix, PERCENTILE_CONT for quartiles,
    and APPROX_COUNT_DISTINCT for cardinality estimation.

    Args:
        table_name: Logical name (unused, kept for API consistency). The CSV
                    is always loaded as ``data``.
        content: Raw CSV bytes.

    Returns:
        dict with keys: correlation_matrix, quartiles, cardinality.
        Empty dict on failure.
    """
    if not HAS_DUCKDB:
        return {}

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_csv_auto(?)",
            [io.StringIO(text)],
        )

        # Discover numeric columns
        columns_info = conn.execute("DESCRIBE data").fetchall()
        numeric_types = {
            "INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT",
            "SMALLINT", "TINYINT", "UBIGINT", "UINTEGER", "USMALLINT",
            "UTINYINT",
        }
        numeric_cols = [
            col_name for col_name, col_type, *_ in columns_info
            if col_type.upper() in numeric_types
        ]

        # --- Correlation matrix ---
        correlation_matrix: dict = {}
        if len(numeric_cols) >= 2:
            for i, col_a in enumerate(numeric_cols):
                correlation_matrix[col_a] = {}
                for col_b in numeric_cols:
                    if col_a == col_b:
                        correlation_matrix[col_a][col_b] = 1.0
                    else:
                        try:
                            val = conn.execute(
                                f'SELECT CORR("{col_a}", "{col_b}") FROM data'
                            ).fetchone()[0]
                            correlation_matrix[col_a][col_b] = (
                                round(float(val), 4) if val is not None else None
                            )
                        except Exception:
                            correlation_matrix[col_a][col_b] = None

        # --- Quartiles (Q1, Q3) ---
        quartiles: dict = {}
        for col in numeric_cols:
            try:
                row = conn.execute(f'''
                    SELECT
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS q1,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS q3
                    FROM data
                    WHERE "{col}" IS NOT NULL
                ''').fetchone()
                quartiles[col] = {
                    "q1": round(float(row[0]), 4) if row[0] is not None else None,
                    "q3": round(float(row[1]), 4) if row[1] is not None else None,
                    "iqr": round(float(row[1]) - float(row[0]), 4) if row[0] is not None and row[1] is not None else None,
                }
            except Exception:
                quartiles[col] = {"q1": None, "q3": None, "iqr": None}

        # --- Approximate cardinality ---
        cardinality: dict = {}
        all_cols = [col_name for col_name, *_ in columns_info]
        for col in all_cols:
            try:
                val = conn.execute(
                    f'SELECT APPROX_COUNT_DISTINCT("{col}") FROM data'
                ).fetchone()[0]
                cardinality[col] = int(val) if val is not None else None
            except Exception:
                cardinality[col] = None

        conn.close()

        logger.info(
            "duckdb_advanced_stats_computed",
            numeric_cols=len(numeric_cols),
            total_cols=len(all_cols),
        )

        return {
            "correlation_matrix": correlation_matrix,
            "quartiles": quartiles,
            "cardinality": cardinality,
        }

    except Exception as e:
        logger.warning("duckdb_advanced_stats_failed", error=str(e))
        return {}


# ---------------------------------------------------------------------------
# Feature 3: Window function analysis
# ---------------------------------------------------------------------------

def compute_window_analysis(
    content: bytes,
    column: str,
    partition_by: Optional[str] = None,
) -> list[dict]:
    """Run window functions on a column and return the results.

    Computes ROW_NUMBER, RANK, PERCENT_RANK, NTILE(4), LAG, and LEAD
    over the specified column, optionally partitioned.

    Args:
        content: Raw CSV bytes.
        column: Column name to analyse.
        partition_by: Optional column name to PARTITION BY.

    Returns:
        List of row dicts with the original column value plus each window
        function result.  Limited to 1000 rows.
    """
    if not HAS_DUCKDB:
        return []

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_csv_auto(?)",
            [io.StringIO(text)],
        )

        partition_clause = f'PARTITION BY "{partition_by}"' if partition_by else ""
        order_clause = f'ORDER BY "{column}"'
        window_spec = f"OVER ({partition_clause} {order_clause})".strip()

        sql = f'''
            SELECT
                "{column}",
                {f'"{partition_by}",' if partition_by else ''}
                ROW_NUMBER() {window_spec} AS row_number,
                RANK() {window_spec} AS rank,
                PERCENT_RANK() {window_spec} AS percent_rank,
                NTILE(4) {window_spec} AS quartile_ntile,
                LAG("{column}") {window_spec} AS lag_value,
                LEAD("{column}") {window_spec} AS lead_value
            FROM data
            LIMIT 1000
        '''

        result = conn.execute(sql)
        col_names = [desc[0] for desc in result.description]
        rows = result.fetchall()
        conn.close()

        output = []
        for row in rows:
            row_dict = {}
            for i, name in enumerate(col_names):
                val = row[i]
                if val is None:
                    row_dict[name] = None
                elif isinstance(val, float):
                    row_dict[name] = round(val, 6)
                else:
                    row_dict[name] = val
            output.append(row_dict)

        logger.info(
            "duckdb_window_analysis_complete",
            column=column,
            partition_by=partition_by,
            rows=len(output),
        )
        return output

    except Exception as e:
        logger.warning("duckdb_window_analysis_failed", error=str(e), column=column)
        return []


# ---------------------------------------------------------------------------
# Feature 4: SUMMARIZE statement
# ---------------------------------------------------------------------------

def summarize_table(content: bytes) -> list[dict]:
    """Run DuckDB's SUMMARIZE statement for a full statistical profile.

    Returns one dict per column with: column_name, column_type, count, min,
    max, approx_unique, avg, std, q25, q50, q75, null_percentage.

    Args:
        content: Raw CSV bytes.

    Returns:
        List of per-column summary dicts.  Empty list on failure.
    """
    if not HAS_DUCKDB:
        return []

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_csv_auto(?)",
            [io.StringIO(text)],
        )

        result = conn.execute("SUMMARIZE data")
        col_names = [desc[0] for desc in result.description]
        rows = result.fetchall()
        conn.close()

        summaries = []
        for row in rows:
            entry = {}
            for i, name in enumerate(col_names):
                val = row[i]
                # Try to coerce numeric strings where appropriate
                if isinstance(val, str):
                    try:
                        val = float(val)
                        if val == int(val):
                            val = int(val)
                    except (ValueError, OverflowError):
                        pass
                entry[name] = val
            summaries.append(entry)

        logger.info("duckdb_summarize_complete", columns=len(summaries))
        return summaries

    except Exception as e:
        logger.warning("duckdb_summarize_failed", error=str(e))
        return []


# ---------------------------------------------------------------------------
# Feature 5: COPY TO export
# ---------------------------------------------------------------------------

def export_data(
    content: bytes,
    format: str = "csv",
    file_path: Optional[str] = None,
) -> dict:
    """Export a CSV dataset to CSV, Parquet, or JSON using DuckDB COPY TO.

    Args:
        content: Raw CSV bytes (source dataset).
        format: Target format -- ``csv``, ``parquet``, or ``json``.
        file_path: Destination path.  If *None*, a temporary file is created.

    Returns:
        dict with ``file_path``, ``format``, ``rows_exported``, ``size_bytes``.
        On failure returns dict with ``error`` key.
    """
    if not HAS_DUCKDB:
        return {"error": "DuckDB not installed"}

    import duckdb

    allowed_formats = {"csv", "parquet", "json"}
    fmt = format.lower()
    if fmt not in allowed_formats:
        return {"error": f"Unsupported format '{format}'. Use: {', '.join(sorted(allowed_formats))}"}

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_csv_auto(?)",
            [io.StringIO(text)],
        )

        row_count = conn.execute("SELECT COUNT(*) FROM data").fetchone()[0]

        # Determine output path
        ext_map = {"csv": ".csv", "parquet": ".parquet", "json": ".json"}
        if file_path is None:
            fd, file_path = tempfile.mkstemp(suffix=ext_map[fmt], prefix="duckdb_export_")
            os.close(fd)

        conn.execute(f"COPY data TO '{file_path}' (FORMAT '{fmt}')")
        conn.close()

        size_bytes = os.path.getsize(file_path)

        logger.info(
            "duckdb_export_complete",
            format=fmt,
            rows=row_count,
            size=size_bytes,
            path=file_path,
        )

        return {
            "file_path": file_path,
            "format": fmt,
            "rows_exported": row_count,
            "size_bytes": size_bytes,
        }

    except Exception as e:
        logger.warning("duckdb_export_failed", error=str(e), format=fmt)
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Feature 6: PIVOT / UNPIVOT
# ---------------------------------------------------------------------------

def pivot_table(
    content: bytes,
    on: str,
    using: str,
    group_by: str,
) -> dict:
    """Pivot a CSV dataset using DuckDB's native PIVOT syntax.

    Args:
        content: Raw CSV bytes.
        on: Column whose distinct values become new columns.
        using: Aggregation expression, e.g. ``SUM(amount)``, ``COUNT(*)``.
        group_by: Column(s) to group by (comma-separated string is fine).

    Returns:
        dict with ``columns``, ``rows`` (list of dicts), ``row_count``.
        On failure returns dict with ``error`` key.
    """
    if not HAS_DUCKDB:
        return {"error": "DuckDB not installed", "rows": [], "columns": []}

    import duckdb

    try:
        text = content.decode("utf-8", errors="replace")
        conn = duckdb.connect(":memory:")
        conn.execute(
            "CREATE TABLE data AS SELECT * FROM read_csv_auto(?)",
            [io.StringIO(text)],
        )

        sql = f'''
            PIVOT data
            ON "{on}"
            USING {using}
            GROUP BY "{group_by}"
        '''

        result = conn.execute(sql)
        col_names = [desc[0] for desc in result.description]
        rows = result.fetchall()
        conn.close()

        formatted_rows = []
        for row in rows[:1000]:
            formatted_rows.append({
                col_names[i]: (
                    round(float(v), 4) if isinstance(v, float) else v
                )
                for i, v in enumerate(row)
            })

        logger.info(
            "duckdb_pivot_complete",
            on=on,
            using=using,
            group_by=group_by,
            rows=len(formatted_rows),
        )

        return {
            "columns": col_names,
            "rows": formatted_rows,
            "row_count": len(formatted_rows),
        }

    except Exception as e:
        logger.warning("duckdb_pivot_failed", error=str(e))
        return {"error": str(e), "rows": [], "columns": []}


# ---------------------------------------------------------------------------
# Feature 7: httpfs extension for URL-based datasets
# ---------------------------------------------------------------------------

def load_url(url: str, format: str = "csv") -> dict:
    """Load a remote dataset from a URL using DuckDB's httpfs extension.

    Installs and loads the httpfs extension, then reads the remote file.

    Args:
        url: Public URL to the dataset (CSV, Parquet, or JSON).
        format: One of ``csv``, ``parquet``, ``json``.

    Returns:
        dict with row_count, column_count, columns, preview, stats, engine.
        Empty dict on failure.
    """
    if not HAS_DUCKDB:
        return {}

    import duckdb

    allowed_formats = {"csv", "parquet", "json"}
    fmt = format.lower()
    if fmt not in allowed_formats:
        logger.warning("duckdb_load_url_bad_format", format=format)
        return {}

    try:
        conn = duckdb.connect(":memory:")

        # Install and load httpfs
        conn.execute("INSTALL httpfs")
        conn.execute("LOAD httpfs")

        reader_map = {
            "csv": "read_csv_auto",
            "parquet": "read_parquet",
            "json": "read_json_auto",
        }
        reader_fn = reader_map[fmt]

        conn.execute(
            f"CREATE TABLE data AS SELECT * FROM {reader_fn}('{url}')"
        )

        result = _extract_table_metadata(conn, "data")
        conn.close()

        logger.info(
            "duckdb_url_loaded",
            url=url,
            format=fmt,
            rows=result.get("row_count"),
        )
        return result

    except Exception as e:
        logger.warning("duckdb_load_url_failed", error=str(e), url=url, format=fmt)
        return {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_table_metadata(conn, table_name: str) -> dict:
    """Extract column metadata, stats, and preview from an already-loaded DuckDB table.

    Shared helper used by load_parquet, load_json, load_url, etc. to avoid
    duplicating the column-iteration logic from parse_csv_duckdb.

    Args:
        conn: An open duckdb.Connection with ``table_name`` already created.
        table_name: Name of the table to inspect.

    Returns:
        dict compatible with parse_csv_duckdb output format.
    """
    numeric_types = {
        "INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT",
        "SMALLINT", "TINYINT", "UBIGINT", "UINTEGER", "USMALLINT",
        "UTINYINT",
    }

    columns_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    columns = []
    stats = {}

    for col_name, col_type, *_ in columns_info:
        sample = conn.execute(
            f'SELECT DISTINCT "{col_name}" FROM {table_name} LIMIT 5'
        ).fetchall()
        sample_values = [str(row[0]) for row in sample if row[0] is not None]

        non_null = conn.execute(
            f'SELECT COUNT("{col_name}") FROM {table_name} WHERE "{col_name}" IS NOT NULL'
        ).fetchone()[0]
        unique = conn.execute(
            f'SELECT COUNT(DISTINCT "{col_name}") FROM {table_name}'
        ).fetchone()[0]

        dtype = "numeric" if col_type.upper() in numeric_types else "text"

        columns.append({
            "name": col_name,
            "dtype": dtype,
            "duckdb_type": col_type,
            "non_null": non_null,
            "unique": unique,
            "sample_values": sample_values,
        })

        if dtype == "numeric":
            try:
                stat_row = conn.execute(f'''
                    SELECT
                        MIN("{col_name}") as min_val,
                        MAX("{col_name}") as max_val,
                        AVG("{col_name}") as avg_val,
                        COUNT("{col_name}") as cnt,
                        STDDEV("{col_name}") as std_val,
                        MEDIAN("{col_name}") as median_val
                    FROM {table_name}
                    WHERE "{col_name}" IS NOT NULL
                ''').fetchone()
                stats[col_name] = {
                    "min": float(stat_row[0]) if stat_row[0] is not None else None,
                    "max": float(stat_row[1]) if stat_row[1] is not None else None,
                    "mean": round(float(stat_row[2]), 4) if stat_row[2] is not None else None,
                    "count": int(stat_row[3]),
                    "std": round(float(stat_row[4]), 4) if stat_row[4] is not None else None,
                    "median": float(stat_row[5]) if stat_row[5] is not None else None,
                }
            except Exception:
                pass

    col_names = [c["name"] for c in columns]
    preview_rows = conn.execute(f"SELECT * FROM {table_name} LIMIT 10").fetchall()
    preview = [
        dict(zip(col_names, [str(v) if v is not None else "" for v in row]))
        for row in preview_rows
    ]

    return {
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "preview": preview,
        "stats": stats,
        "engine": "duckdb",
    }
