"""
DAG Validator using NetworkX - Validates workflow graphs.

Provides proper graph validation, cycle detection, topological sorting,
and path analysis for AI workflows.

Falls back to basic validation if networkx is not installed.
"""

import structlog
from typing import Optional

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
