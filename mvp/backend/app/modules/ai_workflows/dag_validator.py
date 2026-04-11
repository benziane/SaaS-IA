"""
DAG Validator using NetworkX - Validates workflow graphs.

Provides proper graph validation, cycle detection, topological sorting,
path analysis, critical path analysis, parallel execution grouping,
centrality metrics, failure impact analysis, subgraph extraction,
and complexity metrics for AI workflows.

Falls back to basic validation if networkx is not installed.
"""

import structlog
from typing import Any, Optional

logger = structlog.get_logger()


def is_networkx_available() -> bool:
    """Check if networkx is installed."""
    try:
        import networkx  # noqa: F401
        return True
    except ImportError:
        return False


def validate_dag(nodes: list[dict], edges: list[dict]) -> dict:
    """Validate a workflow DAG for correctness.

    Checks:
    - No cycles (must be a DAG)
    - All edge references point to existing nodes
    - All nodes are reachable from start nodes
    - No orphan nodes (disconnected from the graph)

    Returns dict with: valid (bool), errors (list), warnings (list), stats (dict)
    """
    if not nodes:
        return {"valid": True, "errors": [], "warnings": ["Empty workflow"], "stats": {}}

    node_ids = {n["id"] for n in nodes}
    errors = []
    warnings = []

    # Check edge references
    for edge in edges:
        if edge["source"] not in node_ids:
            errors.append(f"Edge source '{edge['source']}' references non-existent node")
        if edge["target"] not in node_ids:
            errors.append(f"Edge target '{edge['target']}' references non-existent node")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "stats": {}}

    # Use networkx if available for proper graph analysis
    if is_networkx_available():
        return _validate_with_networkx(nodes, edges, node_ids)

    # Fallback: basic validation
    return _validate_basic(nodes, edges, node_ids)


def _validate_with_networkx(
    nodes: list[dict], edges: list[dict], node_ids: set[str],
) -> dict:
    """Full DAG validation using networkx."""
    import networkx as nx

    G = nx.DiGraph()
    G.add_nodes_from(node_ids)
    for edge in edges:
        G.add_edge(edge["source"], edge["target"])

    errors = []
    warnings = []

    # Cycle detection
    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        errors.append(f"Graph contains {len(cycles)} cycle(s): {cycles[:3]}")
        return {"valid": False, "errors": errors, "warnings": warnings, "stats": {}}

    # Topological sort (execution order)
    try:
        topo_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        errors.append("Cannot determine execution order (graph is not a DAG)")
        return {"valid": False, "errors": errors, "warnings": warnings, "stats": {}}

    # Find start and end nodes
    start_nodes = [n for n in node_ids if G.in_degree(n) == 0]
    end_nodes = [n for n in node_ids if G.out_degree(n) == 0]

    # Check connectivity
    if len(start_nodes) == 0:
        warnings.append("No start nodes found (all nodes have incoming edges)")

    # Orphan detection
    if not nx.is_weakly_connected(G) and len(node_ids) > 1:
        components = list(nx.weakly_connected_components(G))
        if len(components) > 1:
            warnings.append(f"Graph has {len(components)} disconnected components")

    # Longest path (critical path)
    try:
        longest = nx.dag_longest_path_length(G)
    except Exception:
        longest = 0

    # Parallel branches detection
    parallel_count = sum(1 for n in node_ids if G.out_degree(n) > 1)

    stats = {
        "total_nodes": len(node_ids),
        "total_edges": len(edges),
        "start_nodes": start_nodes,
        "end_nodes": end_nodes,
        "execution_order": topo_order,
        "critical_path_length": longest,
        "parallel_branches": parallel_count,
        "max_depth": longest,
    }

    logger.info("dag_validated_networkx", nodes=len(node_ids), edges=len(edges), valid=True)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def _validate_basic(
    nodes: list[dict], edges: list[dict], node_ids: set[str],
) -> dict:
    """Basic DAG validation without networkx."""
    errors = []
    warnings = []

    # Simple cycle detection via DFS
    adjacency = {}
    in_degree = {nid: 0 for nid in node_ids}
    for edge in edges:
        adjacency.setdefault(edge["source"], []).append(edge["target"])
        if edge["target"] in in_degree:
            in_degree[edge["target"]] += 1

    # Kahn's algorithm for topological sort / cycle detection
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    sorted_nodes = []
    temp_in_degree = dict(in_degree)

    while queue:
        node = queue.pop(0)
        sorted_nodes.append(node)
        for child in adjacency.get(node, []):
            temp_in_degree[child] -= 1
            if temp_in_degree[child] == 0:
                queue.append(child)

    if len(sorted_nodes) != len(node_ids):
        errors.append("Graph contains cycles (not a valid DAG)")

    start_nodes = [nid for nid, deg in in_degree.items() if deg == 0]
    end_nodes = [nid for nid in node_ids if nid not in adjacency or not adjacency[nid]]

    stats = {
        "total_nodes": len(node_ids),
        "total_edges": len(edges),
        "start_nodes": start_nodes,
        "end_nodes": end_nodes,
        "execution_order": sorted_nodes if len(sorted_nodes) == len(node_ids) else [],
        "engine": "basic" if not is_networkx_available() else "networkx",
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def get_execution_order(nodes: list[dict], edges: list[dict]) -> list[str]:
    """Get the topological execution order for workflow nodes."""
    result = validate_dag(nodes, edges)
    return result.get("stats", {}).get("execution_order", [n["id"] for n in nodes])


# ---------------------------------------------------------------------------
# NetworkX graph builder helper
# ---------------------------------------------------------------------------

def _build_graph(nodes: list[dict], edges: list[dict]) -> Optional[Any]:
    """Build a networkx DiGraph from nodes and edges.

    Returns None if networkx is not available.
    """
    if not is_networkx_available():
        logger.warning("networkx_not_available", feature="dag_analysis")
        return None

    import networkx as nx

    G = nx.DiGraph()
    node_ids = {n["id"] for n in nodes}
    G.add_nodes_from(node_ids)
    for edge in edges:
        if edge["source"] in node_ids and edge["target"] in node_ids:
            G.add_edge(edge["source"], edge["target"])
    return G


# ---------------------------------------------------------------------------
# 1. Critical path analysis
# ---------------------------------------------------------------------------

def get_critical_path(nodes: list[dict], edges: list[dict]) -> dict:
    """Compute the critical path (longest path) through the DAG.

    Returns:
        dict with:
        - path: list of node IDs on the critical path
        - length: number of edges on the critical path
        - ancestors: dict mapping each critical-path node to its ancestors
        - descendants: dict mapping each critical-path node to its descendants
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {"path": [], "length": 0, "ancestors": {}, "descendants": {}}

    import networkx as nx

    try:
        if not nx.is_directed_acyclic_graph(G):
            return {"path": [], "length": 0, "ancestors": {}, "descendants": {},
                    "error": "Graph contains cycles"}

        path = nx.dag_longest_path(G)
        length = nx.dag_longest_path_length(G)

        ancestors = {node: sorted(nx.ancestors(G, node)) for node in path}
        descendants = {node: sorted(nx.descendants(G, node)) for node in path}

        logger.info("critical_path_computed", path_length=length, path_nodes=len(path))
        return {
            "path": path,
            "length": length,
            "ancestors": ancestors,
            "descendants": descendants,
        }
    except Exception as exc:
        logger.error("critical_path_error", error=str(exc))
        return {"path": [], "length": 0, "ancestors": {}, "descendants": {},
                "error": str(exc)}


def get_ancestors(nodes: list[dict], edges: list[dict], node: str) -> list[str]:
    """Get all ancestor nodes (upstream dependencies) for a given node."""
    G = _build_graph(nodes, edges)
    if G is None:
        return []

    import networkx as nx

    try:
        if node not in G:
            return []
        return sorted(nx.ancestors(G, node))
    except Exception as exc:
        logger.error("get_ancestors_error", node=node, error=str(exc))
        return []


def get_descendants(nodes: list[dict], edges: list[dict], node: str) -> list[str]:
    """Get all descendant nodes (downstream dependents) for a given node."""
    G = _build_graph(nodes, edges)
    if G is None:
        return []

    import networkx as nx

    try:
        if node not in G:
            return []
        return sorted(nx.descendants(G, node))
    except Exception as exc:
        logger.error("get_descendants_error", node=node, error=str(exc))
        return []


# ---------------------------------------------------------------------------
# 2. Parallel execution analysis
# ---------------------------------------------------------------------------

def get_parallel_groups(nodes: list[dict], edges: list[dict]) -> dict:
    """Identify groups of nodes that can execute concurrently.

    Uses nx.topological_generations to group nodes by dependency level.
    All nodes within the same generation have no dependencies on each other
    and can therefore run in parallel.

    Returns:
        dict with:
        - generations: list of lists (each inner list = nodes runnable in parallel)
        - total_generations: number of sequential steps needed
        - max_parallelism: maximum number of nodes in any single generation
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {"generations": [], "total_generations": 0, "max_parallelism": 0}

    import networkx as nx

    try:
        if not nx.is_directed_acyclic_graph(G):
            return {"generations": [], "total_generations": 0, "max_parallelism": 0,
                    "error": "Graph contains cycles"}

        generations = [sorted(gen) for gen in nx.topological_generations(G)]
        max_parallelism = max((len(gen) for gen in generations), default=0)

        logger.info("parallel_groups_computed",
                     total_generations=len(generations),
                     max_parallelism=max_parallelism)
        return {
            "generations": generations,
            "total_generations": len(generations),
            "max_parallelism": max_parallelism,
        }
    except Exception as exc:
        logger.error("parallel_groups_error", error=str(exc))
        return {"generations": [], "total_generations": 0, "max_parallelism": 0,
                "error": str(exc)}


# ---------------------------------------------------------------------------
# 3. Centrality metrics
# ---------------------------------------------------------------------------

def get_node_importance(nodes: list[dict], edges: list[dict]) -> dict:
    """Compute centrality metrics for each node in the workflow.

    Returns:
        dict with:
        - nodes: dict mapping node_id -> {betweenness, in_degree, out_degree}
        - bottlenecks: list of node IDs with highest betweenness centrality
        - hubs: list of node IDs with highest out_degree centrality
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {"nodes": {}, "bottlenecks": [], "hubs": []}

    import networkx as nx

    try:
        betweenness = nx.betweenness_centrality(G)
        in_deg = nx.in_degree_centrality(G)
        out_deg = nx.out_degree_centrality(G)

        node_metrics = {}
        for nid in G.nodes():
            node_metrics[nid] = {
                "betweenness": round(betweenness.get(nid, 0.0), 4),
                "in_degree": round(in_deg.get(nid, 0.0), 4),
                "out_degree": round(out_deg.get(nid, 0.0), 4),
            }

        # Identify bottlenecks (top betweenness) and hubs (top out_degree)
        if node_metrics:
            max_betweenness = max(m["betweenness"] for m in node_metrics.values())
            max_out_degree = max(m["out_degree"] for m in node_metrics.values())

            bottlenecks = [
                nid for nid, m in node_metrics.items()
                if m["betweenness"] == max_betweenness and max_betweenness > 0
            ]
            hubs = [
                nid for nid, m in node_metrics.items()
                if m["out_degree"] == max_out_degree and max_out_degree > 0
            ]
        else:
            bottlenecks = []
            hubs = []

        logger.info("node_importance_computed", total_nodes=len(node_metrics))
        return {
            "nodes": node_metrics,
            "bottlenecks": bottlenecks,
            "hubs": hubs,
        }
    except Exception as exc:
        logger.error("node_importance_error", error=str(exc))
        return {"nodes": {}, "bottlenecks": [], "hubs": [], "error": str(exc)}


# ---------------------------------------------------------------------------
# 4. Failure impact analysis
# ---------------------------------------------------------------------------

def get_failure_impact(nodes: list[dict], edges: list[dict], node: str) -> dict:
    """Analyze the impact of a node failure on the rest of the workflow.

    Computes all downstream nodes that would be affected if the given node fails.

    Returns:
        dict with:
        - affected_nodes: list of node IDs that depend on the failed node
        - affected_count: number of affected nodes
        - total_nodes: total number of nodes in the workflow
        - impact_percentage: percentage of the workflow affected (0-100)
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {"affected_nodes": [], "affected_count": 0,
                "total_nodes": len(nodes), "impact_percentage": 0.0}

    import networkx as nx

    try:
        if node not in G:
            return {"affected_nodes": [], "affected_count": 0,
                    "total_nodes": G.number_of_nodes(), "impact_percentage": 0.0,
                    "error": f"Node '{node}' not found in graph"}

        affected = sorted(nx.descendants(G, node))
        total = G.number_of_nodes()
        # Impact includes the failed node itself + all descendants
        impact_count = len(affected) + 1
        impact_pct = round((impact_count / total) * 100, 2) if total > 0 else 0.0

        logger.info("failure_impact_computed", node=node,
                     affected=len(affected), impact_pct=impact_pct)
        return {
            "affected_nodes": affected,
            "affected_count": len(affected),
            "total_nodes": total,
            "impact_percentage": impact_pct,
        }
    except Exception as exc:
        logger.error("failure_impact_error", node=node, error=str(exc))
        return {"affected_nodes": [], "affected_count": 0,
                "total_nodes": len(nodes), "impact_percentage": 0.0,
                "error": str(exc)}


# ---------------------------------------------------------------------------
# 5. Subgraph extraction
# ---------------------------------------------------------------------------

def extract_subgraph(
    nodes: list[dict], edges: list[dict], start_node: str,
) -> dict:
    """Extract the downstream subgraph from a given start node.

    Useful for partial workflow re-execution: returns only the portion
    of the graph that is downstream of (and including) start_node.

    Returns:
        dict with:
        - nodes: list of node IDs in the subgraph
        - edges: list of {source, target} dicts in the subgraph
        - execution_order: topological order for the subgraph
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {"nodes": [], "edges": [], "execution_order": []}

    import networkx as nx

    try:
        if start_node not in G:
            return {"nodes": [], "edges": [], "execution_order": [],
                    "error": f"Node '{start_node}' not found in graph"}

        sub_node_ids = {start_node} | nx.descendants(G, start_node)
        sub_G = G.subgraph(sub_node_ids).copy()

        sub_edges = [
            {"source": u, "target": v}
            for u, v in sub_G.edges()
        ]

        try:
            exec_order = list(nx.topological_sort(sub_G))
        except nx.NetworkXUnfeasible:
            exec_order = sorted(sub_node_ids)

        logger.info("subgraph_extracted", start_node=start_node,
                     sub_nodes=len(sub_node_ids), sub_edges=len(sub_edges))
        return {
            "nodes": sorted(sub_node_ids),
            "edges": sub_edges,
            "execution_order": exec_order,
        }
    except Exception as exc:
        logger.error("subgraph_extraction_error", start_node=start_node,
                      error=str(exc))
        return {"nodes": [], "edges": [], "execution_order": [],
                "error": str(exc)}


# ---------------------------------------------------------------------------
# 6. Workflow complexity metrics
# ---------------------------------------------------------------------------

def get_complexity_metrics(nodes: list[dict], edges: list[dict]) -> dict:
    """Compute comprehensive complexity metrics for a workflow DAG.

    Returns:
        dict with:
        - depth: longest path length (critical path depth)
        - total_nodes: number of nodes
        - total_edges: number of edges
        - edge_density: edges / nodes ratio (0 for empty graphs)
        - parallel_branches: number of nodes with out_degree > 1 (fork points)
        - merge_points: number of nodes with in_degree > 1 (join points)
        - max_parallelism: max nodes executable concurrently (via topological_generations)
        - branching_factor: average out_degree of fork nodes
        - weakly_connected_components: number of disconnected subgraphs
    """
    G = _build_graph(nodes, edges)
    if G is None:
        return {
            "depth": 0, "total_nodes": len(nodes), "total_edges": len(edges),
            "edge_density": 0.0, "parallel_branches": 0, "merge_points": 0,
            "max_parallelism": 0, "branching_factor": 0.0,
            "weakly_connected_components": 0,
        }

    import networkx as nx

    try:
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        edge_density = round(total_edges / total_nodes, 2) if total_nodes > 0 else 0.0

        # Depth (critical path length)
        try:
            depth = nx.dag_longest_path_length(G) if nx.is_directed_acyclic_graph(G) else 0
        except Exception:
            depth = 0

        # Fork and merge analysis
        fork_nodes = [n for n in G.nodes() if G.out_degree(n) > 1]
        merge_nodes = [n for n in G.nodes() if G.in_degree(n) > 1]
        parallel_branches = len(fork_nodes)
        merge_points = len(merge_nodes)

        # Branching factor: average out_degree of fork nodes
        if fork_nodes:
            branching_factor = round(
                sum(G.out_degree(n) for n in fork_nodes) / len(fork_nodes), 2
            )
        else:
            branching_factor = 0.0

        # Max parallelism via topological generations
        max_parallelism = 0
        try:
            if nx.is_directed_acyclic_graph(G):
                generations = list(nx.topological_generations(G))
                max_parallelism = max((len(gen) for gen in generations), default=0)
        except Exception:
            max_parallelism = 0

        # Connected components
        num_components = nx.number_weakly_connected_components(G)

        metrics = {
            "depth": depth,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "edge_density": edge_density,
            "parallel_branches": parallel_branches,
            "merge_points": merge_points,
            "max_parallelism": max_parallelism,
            "branching_factor": branching_factor,
            "weakly_connected_components": num_components,
        }

        logger.info("complexity_metrics_computed", **metrics)
        return metrics
    except Exception as exc:
        logger.error("complexity_metrics_error", error=str(exc))
        return {
            "depth": 0, "total_nodes": len(nodes), "total_edges": len(edges),
            "edge_density": 0.0, "parallel_branches": 0, "merge_points": 0,
            "max_parallelism": 0, "branching_factor": 0.0,
            "weakly_connected_components": 0, "error": str(exc),
        }
