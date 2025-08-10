# tests/test_builder.py
import pytest
import math

from geoprocessor.primitives import Point
from geoprocessor.topology import find_face_perimeters

# --- Test Data for find_face_perimeters ---

# Reusable Point objects for crafting graph data
P11, P12, P21, P22 = Point(1, 1), Point(1, 2), Point(2, 1), Point(2, 2)
P33, P34, P43, P44 = Point(3, 3), Point(3, 4), Point(4, 3), Point(4, 4)
P_HG_C = Point(1.5, 1.5)  # Hourglass center
P00, P10, P20 = Point(0, 0), Point(1, 0), Point(2, 0)
P_W_TL, P_W_TR, P_W_BL, P_W_BR = P12, P22, P11, P21
P_W_TM, P_W_BM = Point(1.5, 2), Point(1.5, 1)
P_W_LM, P_W_RM = Point(1, 1.5), Point(2, 1.5)
P_W_C = Point(1.5, 1.5)
P8A, P8B, P8C = Point(0, 1), Point(1, 1), Point(0, 0)
P8D, P8E = Point(1, -1), Point(0, -1)
P_ANT_E = Point(3, 1)  # Dangling/Antenna point

P_AST_C = Point(2, 2)  # Asterisk Center
P_AST_N, P_AST_NE, P_AST_E = Point(2, 3), Point(3, 3), Point(3, 2)
P_AST_SE, P_AST_S, P_AST_SW = Point(3, 1), Point(2, 1), Point(1, 1)
P_AST_W, P_AST_NW = Point(1, 2), Point(1, 3)

# Points for polygon with hole test
P_H_O_BL, P_H_O_BR, P_H_O_TR, P_H_O_TL = Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4) # Outer
P_H_I_BL, P_H_I_BR, P_H_I_TR, P_H_I_TL = Point(1, 1), Point(3, 1), Point(3, 3), Point(1, 3) # Inner

# Reusable calculated distances
D_SQRT_HALF = math.sqrt(0.5)
D_SQRT_2 = math.sqrt(2)
D_2_PLUS_SQRT2 = 2.0 + math.sqrt(2)

# List of Test Cases for find_face_perimeters
FIND_FACE_PERIMETERS_CASES = [
    pytest.param({}, [], id="Empty-Graph"),
    pytest.param(
        {P00: {P10: 1.0}, P10: {P00: 1.0, P20: 1.0}, P20: {P10: 1.0}},
        [],
        id="Line-no-faces"
    ),
    pytest.param({P00: {P10: 1.0}, P10: {P00: 1.0}}, [], id="Bond-2-cycle-not-a-face"),
    pytest.param(
        {
            P11: {P12: 1.0, P21: 1.0},
            P12: {P11: 1.0, P22: 1.0},
            P21: {P11: 1.0, P22: 1.0},
            P22: {P12: 1.0, P21: 1.0},
        },
        [4.0],
        id="Simple-Square"
    ),
    pytest.param(
        {
            P11: {P12: 1, P21: 1}, P12: {P11: 1, P22: 1},
            P21: {P11: 1, P22: 1}, P22: {P12: 1, P21: 1},
            P33: {P34: 1, P43: 1}, P34: {P33: 1, P44: 1},
            P43: {P33: 1, P44: 1}, P44: {P34: 1, P43: 1}
        },
        [4.0, 4.0],
        id="Two-Disconnected-Squares"
    ),
    pytest.param(
        {
            P11: {P21: 1.0, P_HG_C: D_SQRT_HALF},
            P21: {P11: 1.0, P_HG_C: D_SQRT_HALF},
            P12: {P22: 1.0, P_HG_C: D_SQRT_HALF},
            P22: {P12: 1.0, P_HG_C: D_SQRT_HALF},
            P_HG_C: {P11: D_SQRT_HALF, P21: D_SQRT_HALF, P12: D_SQRT_HALF, P22: D_SQRT_HALF}
        },
        [1.0 + 2 * D_SQRT_HALF, 1.0 + 2 * D_SQRT_HALF],
        id="Hourglass-2-triangles"
    ),
    pytest.param(
        {
            P8A: {P8B: 1.0, P8C: 1.0},
            P8B: {P8A: 1.0, P8C: D_SQRT_2},
            P8C: {P8A: 1.0, P8B: D_SQRT_2, P8D: D_SQRT_2, P8E: 1.0},
            P8D: {P8C: D_SQRT_2, P8E: 1.0},
            P8E: {P8C: 1.0, P8D: 1.0}
        },
        [2.0 + D_SQRT_2, 2.0 + D_SQRT_2],
        id="Figure-8"
    ),
    pytest.param(
        {
            P_W_BL: {P_W_LM: 0.5, P_W_BM: 0.5},
            P_W_BR: {P_W_RM: 0.5, P_W_BM: 0.5},
            P_W_TL: {P_W_LM: 0.5, P_W_TM: 0.5},
            P_W_TR: {P_W_RM: 0.5, P_W_TM: 0.5},
            P_W_BM: {P_W_BL: 0.5, P_W_BR: 0.5, P_W_C: 0.5},
            P_W_TM: {P_W_TL: 0.5, P_W_TR: 0.5, P_W_C: 0.5},
            P_W_LM: {P_W_BL: 0.5, P_W_TL: 0.5, P_W_C: 0.5},
            P_W_RM: {P_W_BR: 0.5, P_W_TR: 0.5, P_W_C: 0.5},
            P_W_C: {P_W_BM: 0.5, P_W_TM: 0.5, P_W_LM: 0.5, P_W_RM: 0.5}
        },
        [2.0, 2.0, 2.0, 2.0],
        id="Window-4-small-squares"
    ),
    pytest.param(
        {
            P11: {P12: 1.0, P21: 1.0},
            P12: {P11: 1.0, P22: 1.0},
            P22: {P12: 1.0, P21: 1.0},
            P21: {P11: 1.0, P22: 1.0, P_ANT_E: 1.0}, # Corner with antenna
            P_ANT_E: {P21: 1.0} # Antenna node
        },
        [4.0],
        id="Square-with-Dangling-Edge"
    ),
    pytest.param(
        {
            P_AST_C: {
                P_AST_N: 1.0, P_AST_NE: D_SQRT_2, P_AST_E: 1.0, P_AST_SE: D_SQRT_2,
                P_AST_S: 1.0, P_AST_SW: D_SQRT_2, P_AST_W: 1.0, P_AST_NW: D_SQRT_2
            },
            P_AST_N:  {P_AST_C: 1.0, P_AST_NW: 1.0, P_AST_NE: 1.0},
            P_AST_NE: {P_AST_C: D_SQRT_2, P_AST_N: 1.0, P_AST_E: 1.0},
            P_AST_E:  {P_AST_C: 1.0, P_AST_NE: 1.0, P_AST_SE: 1.0},
            P_AST_SE: {P_AST_C: D_SQRT_2, P_AST_E: 1.0, P_AST_S: 1.0},
            P_AST_S:  {P_AST_C: 1.0, P_AST_SE: 1.0, P_AST_SW: 1.0},
            P_AST_SW: {P_AST_C: D_SQRT_2, P_AST_S: 1.0, P_AST_W: 1.0},
            P_AST_W:  {P_AST_C: 1.0, P_AST_SW: 1.0, P_AST_NW: 1.0},
            P_AST_NW: {P_AST_C: D_SQRT_2, P_AST_W: 1.0, P_AST_N: 1.0},
        },
        [D_2_PLUS_SQRT2] * 8, # 8 identical faces
        id="Complex-Junction-Asterisk"
    ),
    pytest.param(
        {
            # Outer square
            P_H_O_BL: {P_H_O_BR: 4.0, P_H_O_TL: 4.0},
            P_H_O_BR: {P_H_O_BL: 4.0, P_H_O_TR: 4.0},
            P_H_O_TR: {P_H_O_BR: 4.0, P_H_O_TL: 4.0},
            P_H_O_TL: {P_H_O_BL: 4.0, P_H_O_TR: 4.0},
            # Inner square (the hole)
            P_H_I_BL: {P_H_I_BR: 2.0, P_H_I_TL: 2.0},
            P_H_I_BR: {P_H_I_BL: 2.0, P_H_I_TR: 2.0},
            P_H_I_TR: {P_H_I_BR: 2.0, P_H_I_TL: 2.0},
            P_H_I_TL: {P_H_I_BL: 2.0, P_H_I_TR: 2.0},
        },
        [16.0, 8.0],
        id="Polygon-with-hole"
    ),
]


# --- Pytest Test Function ---

@pytest.mark.parametrize("input_graph, expected_perimeters", FIND_FACE_PERIMETERS_CASES)
def test_find_face_perimeters(input_graph, expected_perimeters):
    """
    Tests finding the perimeters of all minimal faces in a planar graph.
    """
    actual_perimeters = find_face_perimeters(input_graph)

    # The order of discovered faces is not guaranteed, so we sort both lists
    # before comparison. `pytest.approx` handles lists of floats gracefully,
    # checking both length and element-wise values with a tolerance.
    assert sorted(actual_perimeters) == pytest.approx(sorted(expected_perimeters))