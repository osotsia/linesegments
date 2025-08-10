# geoprocessor/topology.py
import math
from .primitives import (
    Point,
    GEOMETRIC_TOLERANCE
)


# --- # Helper functions for find_face_perimeters ---
def _calculate_vector_angle(p_from, p_to):
    """
    Calculates the angle in radians of the vector from p_from to p_to
    with respect to the positive x-axis. Angle is in (-pi, pi].
    Assumes p_from and p_to are Point objects.
    """
    return math.atan2(p_to.y - p_from.y, p_to.x - p_from.x)


def _shoelace_area(vertices_ordered):
    """
    Calculates the area of a polygon using the Shoelace formula.
    May need vectorization for large n
    """
    n = len(vertices_ordered)
    if n < 3:
        return 0.0

    p_current = vertices_ordered
    p_next = vertices_ordered[1:] + vertices_ordered[:1]

    area = sum(p1.x * p2.y - p2.x * p1.y for p1, p2 in zip(p_current, p_next))
    return area / 2.0


def _trace_one_face(start_node, first_neighbor, graph):
    """
    Traces a single potential face using the "right-hand rule".

    Starting from the directed edge (start_node -> first_neighbor), it
    repeatedly takes the "sharpest right turn" at each vertex until it
    either returns to the start_node (closing a loop) or fails.

    Args:
        start_node (Point): The starting vertex of the trace.
        first_neighbor (Point): The second vertex, defining the initial direction.
        graph (dict): The adjacency list of the entire graph.

    Returns:
        A tuple (path_nodes, path_perimeter) if a closed loop is found.
        The path_nodes is a list of Point objects, e.g., [A, B, C, A].
        Returns (None, 0) if the trace fails or hits a dead end.
    """
    path_nodes = [start_node]
    path_perimeter = 0.0
    prev_node = start_node
    current_node = first_neighbor

    # Safety break: A simple face cannot have more vertices than the graph itself.
    for _ in range(len(graph) + 1):
        path_nodes.append(current_node)
        path_perimeter += graph[prev_node][current_node]

        # Check if the loop has closed.
        if current_node == start_node:
            return path_nodes, path_perimeter  # Success!

        # --- "Right-Hand Rule" Logic: Find the next node ---
        neighbors = graph[current_node]
        # Reference direction: vector looking backwards along the path we just traveled.
        incoming_angle = _calculate_vector_angle(current_node, prev_node)

        best_next_node = None
        min_turn_angle = float('inf')

        # Sort candidates for deterministic tie-breaking.
        for candidate in sorted(neighbors.keys(), key=lambda p: (p.x, p.y)):
            # Don't immediately go back unless it's a dead-end street.
            if candidate == prev_node and len(neighbors) > 1:
                continue

            outgoing_angle = _calculate_vector_angle(current_node, candidate)
            # The turn angle, normalized to [0, 2*pi). Smallest value is the sharpest right.
            turn_angle = (outgoing_angle - incoming_angle) % (2 * math.pi)

            if turn_angle < min_turn_angle:
                min_turn_angle = turn_angle
                best_next_node = candidate

        if not best_next_node:
            return None, 0  # Trace failed (hit a dead end).

        # Advance the trace.
        prev_node = current_node
        current_node = best_next_node

    return None, 0  # Trace failed (path was too long).


def find_face_perimeters(graph):
    """
    Finds all minimal enclosed areas (faces) in the planar graph and calculates
    their perimeters.

    The algorithm systematically explores the graph:
    1. It attempts to start a face-finding "walk" from every directed edge.
    2. Each walk follows the "right-hand rule": at any intersection, it takes
       the sharpest right turn. This traces the boundary of a face.
    3. Once a walk returns to its start, it has found a closed loop (a potential face).
    4. The loop is validated to ensure it's a real, internal, simple polygon.
    5. The perimeters of valid faces are collected.
    """
    perimeters = []
    visited_directed_edges = set()
    found_faces = set()

    # Systematically try every directed edge as a starting point.
    for start_node in graph:
        # Sort neighbors for deterministic behavior.
        for first_neighbor in sorted(graph[start_node].keys(), key=lambda p: (p.x, p.y)):
            start_edge = (start_node, first_neighbor)
            if start_edge in visited_directed_edges:
                continue

            # Attempt to trace one face starting from this edge.
            path, perimeter = _trace_one_face(start_node, first_neighbor, graph)

            # If a closed path was found, validate it.
            if path:
                # The path includes the repeated start_node at the end, e.g., [A, B, C, A].
                # For validation, we use the unique nodes, e.g., [A, B, C].
                unique_ordered_nodes = path[:-1]
                canonical_face = frozenset(unique_ordered_nodes)

                # Validation 1: Is it a simple polygon with at least 3 vertices?
                # (Path doesn't cross itself before closing).
                is_simple_polygon = (len(canonical_face) >= 3 and
                                     len(canonical_face) == len(unique_ordered_nodes))

                if not is_simple_polygon:
                    continue

                # Validation 2: Is it an internal face and not already found?
                if canonical_face not in found_faces:
                    # The "right-hand rule" traces internal faces clockwise, giving negative area.
                    signed_area = _shoelace_area(unique_ordered_nodes)
                    if signed_area < -GEOMETRIC_TOLERANCE:
                        perimeters.append(perimeter)
                        found_faces.add(canonical_face)

                        # Optimization: Mark all edges of this new face as visited.
                        for i in range(len(path) - 1):
                            visited_directed_edges.add((path[i], path[i + 1]))
    return perimeters
