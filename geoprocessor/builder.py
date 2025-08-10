# geoprocessor/builder.py
import math
from .primitives import (
    Point,
    euclidean_dist,
    GEOMETRIC_TOLERANCE,
    POINT_PRECISION_DECIMALS
)


def _get_segment_intersection(segment1, segment2):
    """
    Calculates the intersection point of two line segments, if it exists
    and lies on both segments.

    This function uses vector parametric equations. A line segment is represented as a
    starting point plus a fraction of a direction vector. It solves for the values
    ('t' and 'u') that would make the two lines meet, and then checks if those values
    are between 0 and 1, which confirms the intersection lies on both segments.

    TODO: has issues with overlapping segments, see tests

    Args:
        segment1 (tuple): A tuple (P1, P2) where P1 and P2 are Point objects.
        segment2 (tuple): A tuple (P3, P4) where P3 and P4 are Point objects.

    Returns:
        Point or None: The intersection Point object if the segments intersect,
                       otherwise None. Returns None for collinear segments as per
                       the problem's context (endpoints and graph building handle these).
    """

    p1, p2 = segment1
    p3, p4 = segment2

    # Define the direction vectors for the segments
    dir1 = p2 - p1  # Direction vector for segment 1
    dir2 = p4 - p3  # Direction vector for segment 2

    def calc_signed_parallelogram_area(v1, v2):
        """
        Calculates the signed area of the parallelogram formed by two 2D vectors.

        See: https://en.wikipedia.org/wiki/Cross_product#Geometric_meaning

        This is commonly known as the "2D cross product". It is derived by
        treating the 2D vectors v1=(x1, y1) and v2=(x2, y2) as 3D vectors
        v1'=(x1, y1, 0) and v2'=(x2, y2, 0) and then calculating the Z-component
        of their 3D cross product (v1' × v2').

        The resulting scalar value is extremely useful for determining the relative
        orientation of the two vectors.

        - The sign of the result indicates orientation:
          - > 0: The turn from v1 to v2 is counter-clockwise (v2 is "left" of v1).
          - < 0: The turn from v1 to v2 is clockwise (v2 is "right" of v1).
          - = 0: The vectors are collinear (lie on the same line).

        - The absolute value of the result is the area of the parallelogram
          spanned by the two vectors.

        Args:
            v1 (Point): The first 2D vector, represented as a Point object.
            v2 (Point): The second 2D vector, represented as a Point object.

        Returns:
            float: The scalar value (z-component) of the 3D cross product,
                   which corresponds to the signed area of the parallelogram.
        """
        return v1.x * v2.y - v1.y * v2.x

    den = calc_signed_parallelogram_area(dir1, dir2)

    if math.isclose(den, 0.0, abs_tol=GEOMETRIC_TOLERANCE):
        # Lines are parallel or collinear.
        return None

    # Vector from the start of segment 1 to the start of segment 2
    p1_p3 = p3 - p1

    # 't' is the fractional distance along segment1 where the infinite lines intersect.
    # It is derived from solving the system of linear equations: p1 + t*dir1 = p3 + u*dir2.
    # (take the cross product of the equation with dir2)
    # Same idea for 'u'

    t = calc_signed_parallelogram_area(p1_p3, dir2) / den
    u = calc_signed_parallelogram_area(p1_p3, dir1) / den

    # Check if intersection is within both segments (0 <= t <= 1 and 0 <= u <= 1)
    # The epsilon check handles floating point inaccuracies at segment endpoints.
    if (-GEOMETRIC_TOLERANCE <= t <= 1 + GEOMETRIC_TOLERANCE) and (-GEOMETRIC_TOLERANCE <= u <= 1 + GEOMETRIC_TOLERANCE):
        # Calculate the intersection point by starting at p1 and moving t-fraction
        # along the direction vector dir1.
        return p1 + (dir1 * t)

    return None


def _create_point_cache_and_factory():
    """
    Creates and returns a cache and a corresponding factory function for generating unique,
    canonical Point objects, handling floating-point inaccuracies.
    """
    point_cache = {}

    def get_canonical_point(x, y):
        """
        Ensures that for any given (x,y) coordinates (within precision),
        the same Point object instance is returned.
        """
        # A key based on rounded coordinates ensures "close" points map to the same entry.
        cache_key = (round(x, POINT_PRECISION_DECIMALS), round(y, POINT_PRECISION_DECIMALS))
        if cache_key not in point_cache:
            point_cache[cache_key] = Point(x, y)
        return point_cache[cache_key]

    return point_cache, get_canonical_point


def find_all_vertices_and_segment_map(raw_input_segments):
    """
    Pre-processes raw line segments to find all unique vertices (endpoints and
    intersections) and map them back to the segments they lie on.

    This process is like a land survey:
    1.  **Process Endpoints**: It first identifies the start and end "corners" of each segment.
    2.  **Find Intersections**: It then checks every pair of segments for "crossings".
    3.  **Catalog Results**: It produces a "map" that shows which points lie on which original segment
            and a set of all unique points found.

    A key feature is the use of a "canonical point factory" to ensure that points
    with tiny floating-point differences are treated as the same single vertex.

    Args:
        raw_input_segments (iterable): An iterable of segments, e.g., [((x1,y1),(x2,y2)), ...].

    Returns:
        tuple: (all_vertices, segment_to_points_map, point_cache)
            - segment_to_points_map (dict): Maps raw segment tuples to sets of canonical Points. Main result.
            - all_vertices (set): A set of unique canonical Point objects. Redundant, but still useful.
            - point_cache (dict): The cache used to create the points, for use in later steps.
    """
    point_cache, get_canonical_point = _create_point_cache_and_factory()
    all_vertices = set()
    segment_to_points_map = {}
    canonical_segments = []  # Will store segments with canonical Point objects for intersection tests

    # --- Phase 1: Process Endpoints ---
    for raw_segment in raw_input_segments:
        p1_coords, p2_coords = raw_segment

        p1 = get_canonical_point(p1_coords[0], p1_coords[1])
        p2 = get_canonical_point(p2_coords[0], p2_coords[1])

        # Add endpoints to the master set of all vertices
        all_vertices.add(p1)
        all_vertices.add(p2)

        # Map the original raw segment to its canonical endpoints.
        segment_to_points_map[raw_segment] = {p1, p2}

        # Store the canonical version for intersection checking, ignoring zero-length segments.
        if p1 != p2:
            canonical_segments.append({'original': raw_segment, 'canonical': (p1, p2)})

    # --- Phase 2: Find and Add Intersections ---
    # O(N^2) comparison of every segment against every other.
    for i in range(len(canonical_segments)):
        for j in range(i + 1, len(canonical_segments)):
            seg_a_data = canonical_segments[i]
            seg_b_data = canonical_segments[j]

            intersection = _get_segment_intersection(
                seg_a_data['canonical'],
                seg_b_data['canonical']
            )

            if intersection:
                # Get its canonical representation.
                ip = get_canonical_point(intersection.x, intersection.y)

                # Add the new vertex to the master set.
                all_vertices.add(ip)

                # Add the intersection vertex to the maps of BOTH segments that formed it.
                segment_to_points_map[seg_a_data['original']].add(ip)
                segment_to_points_map[seg_b_data['original']].add(ip)

    return segment_to_points_map, all_vertices, point_cache


# 2. Construct Planar Graph
def _get_reference_point(raw_seg_tuple, points_on_segment, point_cache):
    """
    Finds a reliable canonical Point object to use as a sorting reference.

    It tries strategies in order of reliability:
    1. Direct lookup in the point_cache using original coordinates. (Most reliable)
    2. Search within the `points_on_segment` set for a matching point. (Good fallback)
    3. Pick an arbitrary point from the set. (Last resort)

    Returns:
        A canonical Point object or None if the set is empty.
    """
    start_coords = raw_seg_tuple[0]

    # Strategy 1: Use the cache for a direct, reliable lookup.
    if point_cache:
        rounded_key = (round(start_coords[0], POINT_PRECISION_DECIMALS),
                       round(start_coords[1], POINT_PRECISION_DECIMALS))
        ref_point = point_cache.get(rounded_key)
        if ref_point:
            return ref_point

    # Strategy 2: Fallback to searching the set if cache fails or is absent.
    # This is less efficient but robust.
    temp_start_point = Point(start_coords[0], start_coords[1])
    for p in points_on_segment:
        if p == temp_start_point:  # Uses custom Point.__eq__ for float-safe comparison
            return p

    # Strategy 3: Last resort. If the original endpoint wasn't found (highly unlikely),
    # any point on the collinear set will work as a sort reference.
    if points_on_segment:
        return list(points_on_segment)[0]

    return None  # Should not be reached if len(points_on_segment) >= 2


def build_graph(segment_to_points_map, all_vertices_set, point_cache_for_ref_lookup=None):
    """
    Builds an adjacency list graph representing the planar arrangement of line segments.

    This function operates like assembling "beads on a string":
    1.  It considers each original line segment as a "string".
    2.  The set of points on that segment (endpoints + intersections) are the "beads".
    3.  It sorts these beads into their correct linear order along the string.
    4.  It creates graph edges connecting each bead to its immediate neighbor on the string.

    Args:
        segment_to_points_map (dict): Maps each original segment to a set of
                                      all canonical Point objects that lie on it.
        all_vertices_set (set): A set of all unique canonical Point objects (vertices).
        point_cache_for_ref_lookup (dict, optional): The cache used to create the
                                      canonical points, for reliable lookups.

    Returns:
        dict: An adjacency list where keys are Point objects and values are dictionaries
              of {neighbor_point: distance}.
    """

    # Initialize the graph structure with all known vertices.
    adj_list = {vertex: {} for vertex in all_vertices_set}

    # Iterate over each original segment and its collection of associated vertices.
    for raw_seg_tuple, points_on_segment in segment_to_points_map.items():
        # A line in the graph requires at least two vertices.
        if len(points_on_segment) < 2:
            continue

        # == THE CORE LOGIC ==
        # 1. Find a reference point to allow sorting of the collinear points.
        ref_point = _get_reference_point(raw_seg_tuple, points_on_segment, point_cache_for_ref_lookup)
        if not ref_point:
            continue  # Should not happen if input is valid.

        # 2. Sort the points along the segment by their distance from the reference point.
        # This puts the "beads" in the correct order on their "string".
        sorted_points = sorted(list(points_on_segment), key=lambda p: euclidean_dist(ref_point, p))

        # 3. Create edges between adjacent points in the sorted list.
        # These are the "atomic" sub-segments of the original line.
        for i in range(len(sorted_points) - 1):
            u = sorted_points[i]
            v = sorted_points[i + 1]

            distance = euclidean_dist(u, v)

            # Only add an edge if the points are distinct, avoiding zero-length edges.
            if distance > GEOMETRIC_TOLERANCE:
                # Add the undirected edge to the graph.
                adj_list[u][v] = distance
                adj_list[v][u] = distance

    return adj_list
