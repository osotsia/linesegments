# tests/test_builder.py

import pytest
import math

from geoprocessor.primitives import Point, GEOMETRIC_TOLERANCE, POINT_PRECISION_DECIMALS
from geoprocessor.builder import (
    _get_segment_intersection,
    find_all_vertices_and_segment_map,
    build_graph,
)

# --- Test Data for _get_segment_intersection ---

# Reusable Segment Library
segments = {
    "main_diag": (Point(0, 0), Point(2, 2)),
    "anti_diag": (Point(0, 2), Point(2, 0)),
    "horizontal_base": (Point(0, 0), Point(2, 0)),
    "horizontal_parallel": (Point(0, 1), Point(2, 1)),
    "vertical_at_1": (Point(1, -1), Point(1, 1)),
    "vertical_at_2": (Point(2, -1), Point(2, 1)),
}

# List of Test Cases for _get_segment_intersection
SEGMENT_INTERSECTION_CASES = [
    pytest.param(segments["main_diag"], segments["anti_diag"], Point(1, 1), id="Simple-X-intersection"),
    pytest.param(segments["horizontal_base"], segments["vertical_at_1"], Point(1, 0), id="H-V-intersection"),
    pytest.param(segments["horizontal_base"], segments["vertical_at_2"], Point(2, 0), id="Intersection-at-endpoint"),
    pytest.param(segments["horizontal_base"], (Point(2, 0), Point(3, 1)), Point(2, 0),
                 id="Shared-endpoint-intersection"),
    pytest.param(segments["horizontal_base"], segments["horizontal_parallel"], None, id="Parallel-no-intersection"),
    pytest.param((Point(0, 0), Point(2, 0)), (Point(3, 0), Point(4, 0)), None, id="Collinear-disjoint"),
    pytest.param(segments["horizontal_base"], (Point(0.5, 0), Point(1.5, 0)), None, id="Collinear-overlapping"),
    pytest.param(segments["main_diag"], segments["main_diag"], None, id="Identical-segments-collinear"),
    pytest.param(segments["main_diag"], (segments["main_diag"][1], segments["main_diag"][0]), None,
                 id="Identical-segments-reversed-collinear"),
    pytest.param((Point(0, 0), Point(1, 1)), (Point(2, 2), Point(3, 3)), None, id="Lines-same-segments-disjoint"),
    pytest.param((Point(1, 1), Point(2, 2)), (Point(1, 2), Point(2, 1)), Point(1.5, 1.5), id="Hourglass-diagonals"),
    pytest.param((Point(0, 0), Point(1, 2)), (Point(0, 1), Point(1, 0)), Point(1 / 3, 2 / 3),
                 id="Floating-point-1/3-2/3"),
    pytest.param(
        (Point(0, 0), Point(1, 0)),
        (Point(1.0 - (GEOMETRIC_TOLERANCE * 100), -1), Point(1.0 - (GEOMETRIC_TOLERANCE * 100), 1)),
        Point(1.0 - (GEOMETRIC_TOLERANCE * 100), 0),
        id="Intersection-near-endpoint-within-tolerance"
    ),
]

# --- Test Data for find_all_vertices_and_segment_map ---

# Reusable canonical Point objects for crafting expected results
P_0_0, P_2_0 = Point(0, 0), Point(2, 0)
P_1_neg1, P_1_1 = Point(1, -1), Point(1, 1)
P_0_2, P_2_2 = Point(0, 2), Point(2, 2)
P_1_0 = Point(1, 0)
P_1_2 = Point(1, 2)
P_3_3, P_4_0 = Point(3, 3), Point(4, 0)

# Reusable raw segment tuples (matching input format)
RAW_H = ((0.0, 0.0), (2.0, 0.0))
RAW_V = ((1.0, -1.0), (1.0, 1.0))
RAW_T_STEM = ((1.0, 0.0), (1.0, 2.0))
RAW_PARALLEL = ((0.0, -2.0), (2.0, -2.0))
RAW_DEGENERATE = ((3.0, 3.0), (3.0, 3.0))
RAW_V_TOUCHING = ((2.0, 0.0), (2.0, 2.0))

# List of Test Cases for find_all_vertices_and_segment_map
FIND_ALL_VERTICES_CASES = [
    pytest.param([], set(), {}, id="Empty-input"),
    pytest.param([RAW_H], {P_0_0, P_2_0}, {RAW_H: {P_0_0, P_2_0}}, id="Single-segment"),
    pytest.param(
        [RAW_H, RAW_PARALLEL],
        {P_0_0, P_2_0, Point(0, -2), Point(2, -2)},
        {RAW_H: {P_0_0, P_2_0}, RAW_PARALLEL: {Point(0, -2), Point(2, -2)}},
        id="Two-non-intersecting-parallel-segments"
    ),
    pytest.param(
        [RAW_H, RAW_V],
        {P_0_0, P_2_0, P_1_neg1, P_1_1, P_1_0},
        {RAW_H: {P_0_0, P_2_0, P_1_0}, RAW_V: {P_1_neg1, P_1_1, P_1_0}},
        id="Simple-cross-intersection"
    ),
    pytest.param(
        [RAW_H, RAW_T_STEM],
        {P_0_0, P_2_0, P_1_0, P_1_2},
        {RAW_H: {P_0_0, P_2_0, P_1_0}, RAW_T_STEM: {P_1_0, P_1_2}},
        id="T-junction-endpoint-on-segment"
    ),
    pytest.param([RAW_H, RAW_V_TOUCHING], {P_0_0, P_2_0, P_2_2},
                 {RAW_H: {P_0_0, P_2_0}, RAW_V_TOUCHING: {P_2_0, P_2_2}}, id="V-shape-shared-endpoint"),
    pytest.param(
        [RAW_H, RAW_DEGENERATE],
        {P_0_0, P_2_0, P_3_3},
        {RAW_H: {P_0_0, P_2_0}, RAW_DEGENERATE: {P_3_3}},
        id="Input-with-degenerate-segment"
    ),
    #pytest.param(
    #    [((0, 0), (2, 0)), ((1, 0), (3, 0))],
    #    {Point(0, 0), Point(1, 0), Point(2, 0), Point(3, 0)},
    #    {((0, 0), (2, 0)): {Point(0, 0), Point(1, 0), Point(2, 0)}, ((1, 0), (3, 0)): {Point(1, 0), Point(2, 0), Point(3, 0)}},
    #    id="Collinear-overlapping-segments"
    #),
    #pytest.param(
    #    [((0, 0), (4, 0)), ((1, 0), (2, 0))],
    #    {Point(0, 0), Point(1, 0), Point(2, 0), Point(4, 0)},
    #    {((0, 0), (4, 0)): {Point(0, 0), Point(1, 0), Point(2, 0), Point(4, 0)}, ((1, 0), (2, 0)): {Point(1, 0), Point(2, 0)}},
    #    id="Contained-segment"
    #),

]

# --- Test Data for build_graph ---

# Reusable Point objects for build_graph tests
P_0_0, P_1_0, P_2_0, P_3_0 = Point(0, 0), Point(1, 0), Point(2, 0), Point(3, 0)
P_1_neg1, P_1_1 = Point(1, -1), Point(1, 1)
P_0_2, P_2_2 = Point(0, 2), Point(2, 2)
P_1_1_diag, P_3_3_diag, P_4_4_diag = Point(1, 1), Point(3, 3), Point(4, 4)
P_5_5 = Point(5, 5)

# Reusable calculated distances
DIST_SQRT2 = math.sqrt(2)
DIST_2_SQRT2 = 2 * math.sqrt(2)

# List of Test Cases for build_graph
BUILD_GRAPH_CASES = [
    pytest.param({}, set(), {}, id="Empty-input"),
    pytest.param({}, {P_0_0, P_5_5}, {P_0_0: {}, P_5_5: {}}, id="Isolated-vertices-no-segments"),
    pytest.param(
        {((0, 0), (3, 0)): {P_0_0, P_3_0}},
        {P_0_0, P_3_0},
        {P_0_0: {P_3_0: 3.0}, P_3_0: {P_0_0: 3.0}},
        id="Single-segment-no-intersections"
    ),
    pytest.param(
        {((0, 0), (2, 0)): {P_0_0, P_2_0, P_1_0}, ((1, -1), (1, 1)): {P_1_neg1, P_1_1, P_1_0}},
        {P_0_0, P_2_0, P_1_0, P_1_neg1, P_1_1},
        {
            P_0_0: {P_1_0: 1.0},
            P_2_0: {P_1_0: 1.0},
            P_1_neg1: {P_1_0: 1.0},
            P_1_1: {P_1_0: 1.0},
            P_1_0: {P_0_0: 1.0, P_2_0: 1.0, P_1_neg1: 1.0, P_1_1: 1.0}
        },
        id="T-Junction"
    ),
    pytest.param(
        {((0, 0), (2, 2)): {P_0_0, P_2_2, P_1_1_diag}, ((0, 2), (2, 0)): {P_0_2, P_2_0, P_1_1_diag}},
        {P_0_0, P_2_2, P_0_2, P_2_0, P_1_1_diag},
        {
            P_0_0: {P_1_1_diag: DIST_SQRT2},
            P_2_2: {P_1_1_diag: DIST_SQRT2},
            P_0_2: {P_1_1_diag: DIST_SQRT2},
            P_2_0: {P_1_1_diag: DIST_SQRT2},
            P_1_1_diag: {P_0_0: DIST_SQRT2, P_2_2: DIST_SQRT2, P_0_2: DIST_SQRT2, P_2_0: DIST_SQRT2}
        },
        id="Cross-X"
    ),
    pytest.param(
        {((0, 0), (4, 4)): {P_0_0, P_1_1_diag, P_3_3_diag, P_4_4_diag}},
        {P_0_0, P_1_1_diag, P_3_3_diag, P_4_4_diag},
        {
            P_0_0: {P_1_1_diag: DIST_SQRT2},
            P_1_1_diag: {P_0_0: DIST_SQRT2, P_3_3_diag: DIST_2_SQRT2},
            P_3_3_diag: {P_1_1_diag: DIST_2_SQRT2, P_4_4_diag: DIST_SQRT2},
            P_4_4_diag: {P_3_3_diag: DIST_SQRT2}
        },
        id="Line-with-multiple-collinear-points"
    ),
]


# ==========================
# --- Custom Assertions ----
# ==========================

def assert_graphs_are_close(actual, expected):
    """
    Asserts that two graphs are almost equal.

    This helper is needed because the graph is a nested dictionary with
    float values (edge weights) that require approximate comparison.
    `pytest.approx` does not support nested structures directly.
    """
    # 1. Compare the set of vertices (the top-level keys)
    assert actual.keys() == expected.keys(), "Graph vertex sets do not match"

    # 2. Iterate through each vertex and compare its neighbors and edge weights
    for vertex, expected_neighbors in expected.items():
        actual_neighbors = actual[vertex]

        # 2a. Compare the set of neighbors for the current vertex
        assert actual_neighbors.keys() == expected_neighbors.keys(), \
            f"Neighbors for vertex {vertex} do not match"

        # 2b. Compare the edge weights for each neighbor with a tolerance
        for neighbor, expected_weight in expected_neighbors.items():
            actual_weight = actual_neighbors[neighbor]
            assert actual_weight == pytest.approx(expected_weight), \
                f"Edge weight for ({vertex} -> {neighbor}) does not match"


# ==========================
# --- Pytest Test Functions ---
# ==========================

@pytest.mark.parametrize("segment1, segment2, expected", SEGMENT_INTERSECTION_CASES)
def test_get_segment_intersection(segment1, segment2, expected):
    """
    Tests the _get_segment_intersection function with various cases.
    """
    actual = _get_segment_intersection(segment1, segment2)
    assert actual == expected


@pytest.mark.parametrize("input_segments, expected_vertices, expected_map", FIND_ALL_VERTICES_CASES)
def test_find_all_vertices_and_segment_map(input_segments, expected_vertices, expected_map):
    """
    Tests finding all vertices and mapping them back to their parent segments.
    """
    actual_map, actual_vertices, _ = find_all_vertices_and_segment_map(input_segments)

    assert actual_vertices == expected_vertices
    assert actual_map == expected_map


@pytest.mark.parametrize("input_seg_map, input_v_set, expected_graph", BUILD_GRAPH_CASES)
def test_build_graph(input_seg_map, input_v_set, expected_graph):
    """
    Tests the construction of the graph from a segment map and vertex set.
    """
    point_cache = {
        (round(p.x, POINT_PRECISION_DECIMALS), round(p.y, POINT_PRECISION_DECIMALS)): p
        for p in input_v_set
    }

    actual_graph = build_graph(input_seg_map, input_v_set, point_cache)

    # Use the custom helper to compare the graphs with tolerance for edge weights
    assert_graphs_are_close(actual_graph, expected_graph)
