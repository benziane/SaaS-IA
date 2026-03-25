"""
DuckDB Engine - Fast in-memory SQL analytics for datasets.

Replaces pandas for data analysis:
- 100x faster on large CSV files
- SQL queries (LLMs generate better SQL than pandas code)
- In-memory, zero server setup
- Auto-profiling with ydata-profiling

Falls back gracefully to the existing pandas/CSV parser if not installed.
"""

import io
import json
from typing import Optional

import structlog

logger = structlog.get_logger()


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
