"""Canonical world-node graph for travel between locations."""
CITY_NODE = "city"
TRAVEL_SECONDS = 60

WORLD_NODES = {
    "city": {"id": "city", "name": "🏙️ Місто", "kind": "city", "huntable": False},
    "start_path": {"id": "start_path", "name": "🌿 Початок Шляху", "kind": "location", "huntable": True},
    "dark_forest": {"id": "dark_forest", "name": "🌲 Темний Бір", "kind": "location", "huntable": True},
}

LOCATION_GRAPH = {
    "city": ("start_path",),
    "start_path": ("city", "dark_forest"),
    "dark_forest": ("start_path",),
}

def get_world_node(node_id):
    return WORLD_NODES.get(str(node_id))

def get_adjacent_nodes(node_id):
    return tuple(LOCATION_GRAPH.get(str(node_id), ()))

def are_adjacent(from_node, to_node):
    return str(to_node) in get_adjacent_nodes(from_node)

def validate_location_graph():
    errors=[]
    for node, neighbors in LOCATION_GRAPH.items():
        if node not in WORLD_NODES: errors.append(f"unknown graph node: {node}")
        if len(neighbors) != len(set(neighbors)): errors.append(f"duplicate edge from: {node}")
        for neighbor in neighbors:
            if neighbor not in WORLD_NODES: errors.append(f"unknown neighbor: {neighbor}")
            elif node not in LOCATION_GRAPH.get(neighbor, ()): errors.append(f"asymmetric edge: {node}->{neighbor}")
    if set(WORLD_NODES) != set(LOCATION_GRAPH): errors.append("WORLD_NODES and LOCATION_GRAPH keys differ")
    if errors: raise ValueError("; ".join(errors))
    return True

validate_location_graph()
