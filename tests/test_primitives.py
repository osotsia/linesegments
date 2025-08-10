# tests/test_primitives.py

import pytest
import math
from geoprocessor.primitives import Point, euclidean_dist, GEOMETRIC_TOLERANCE, POINT_PRECISION_DECIMALS

# ==========================
# --- Reusable Test Data ---
# ==========================

# A collection of common Point objects to be reused across multiple tests.
# This improves readability and makes the test suite easier to maintain.
P_0_0 = Point(0, 0)
P_1_2 = Point(1, 2)
P_2_1 = Point(2, 1)
P_3_4 = Point(3, 4)
P_5_5 = Point(5, 5)
P_1_1 = Point(1, 1)
P_NEG1_0 = Point(-1, 0)
P_2_0 = Point(2, 0)
P_NEG1_NEG1 = Point(-1, -1)
P_5_10 = Point(5, 10)
P_1_3 = Point(1, 3)
P_1_NEG3 = Point(1, -3)
P_2_NEG3 = Point(2, -3)


# =================================================================
# --- Test Cases for Representation (`__repr__`) ---
# =================================================================

# This list is generated dynamically to be robust against changes in POINT_PRECISION_DECIMALS.
REPR_TEST_CASES = []

# The format specifier width used in the Point's __repr__ method.
REPR_WIDTH = POINT_PRECISION_DECIMALS + 1

# Case 1: Simple integer coordinates
p1 = Point(1, 2)
expected1 = f"Point({p1.x:.{REPR_WIDTH}f}, {p1.y:.{REPR_WIDTH}f})"
REPR_TEST_CASES.append(
    pytest.param(p1, expected1, id="Integer-coords")
)

# Case 2: Floating point coordinates that require padding and rounding
p2 = Point(1 / 3, -5.678)
expected2 = f"Point({p2.x:.{REPR_WIDTH}f}, {p2.y:.{REPR_WIDTH}f})"
REPR_TEST_CASES.append(
    pytest.param(p2, expected2, id="Float-coords")
)


# =================================================================
# --- Dynamically Generated Test Cases for Precision Edge Cases ---
# =================================================================

# Create constants based on the precision decimal to drive the tests.
# A value far smaller than the rounding precision.
TINY_DELTA = 10 ** -(POINT_PRECISION_DECIMALS + 2)
# The coordinate where rounding behavior changes (e.g., 0.00000005 for D=7).
ROUNDING_BOUNDARY = 0.5 * (10 ** -POINT_PRECISION_DECIMALS)

# --- Test Cases for Equality (`__eq__`) ---
EQUALITY_TEST_CASES = [
    # Simple, non-precision-dependent cases
    pytest.param(P_1_2, Point(1, 2), True, id="identical-points"),
    pytest.param(P_1_2, P_2_1, False, id="different-points"),
    pytest.param(P_1_2, (1, 2), False, id="compare-to-tuple"),

    # Dynamic Case 1: Points that are technically different but should be EQUAL
    # because they fall within the same rounding precision.
    pytest.param(
        Point(1.1, 2.2),
        Point(1.1 + TINY_DELTA, 2.2 - TINY_DELTA),
        True,
        id="equality-within-precision"
    ),

    # Dynamic Case 2: Points that are very close but should be NOT EQUAL
    # because they fall on opposite sides of a rounding boundary.
    pytest.param(
        Point(ROUNDING_BOUNDARY - TINY_DELTA, 0),
        Point(ROUNDING_BOUNDARY + TINY_DELTA, 0),
        False,
        id="inequality-across-rounding-boundary"
    ),
]

# =================================================================
# --- Test Cases for Hashing (`__hash__`) ---
# =================================================================

HASH_TEST_CASES = [
    # Simple, non-precision-dependent cases
    pytest.param(P_1_2, Point(1, 2), True, id="hash-of-identical-points"),
    pytest.param(P_1_2, P_2_1, False, id="hash-of-different-points"),

    # Dynamic Case 1: Points that are different but should have the SAME HASH
    # because they fall within the same rounding precision.
    pytest.param(
        Point(1.1, 2.2),
        Point(1.1 + TINY_DELTA, 2.2),
        True,
        id="hash-of-close-points-within-precision"
    ),

    # Dynamic Case 2: Points that are very close but should have DIFFERENT HASHES
    # because they fall on opposite sides of a rounding boundary.
    pytest.param(
        Point(ROUNDING_BOUNDARY - TINY_DELTA, 0),
        Point(ROUNDING_BOUNDARY + TINY_DELTA, 0),
        False,
        id="hash-of-points-across-rounding-boundary"
    ),
]


# ==========================
# --- Tests for Point Class ---
# ==========================

class TestPoint:
    """Groups tests for the Point class."""

    def test_initialization(self):
        """Tests that Point initializes with float coordinates and as_tuple works."""
        p = Point(1, -2.5)
        assert p.x == 1.0
        assert p.y == -2.5
        assert p.as_tuple() == (1.0, -2.5)

    @pytest.mark.parametrize("p, expected_repr", REPR_TEST_CASES)
    def test_repr(self, p, expected_repr):
        """
        Tests the __repr__ method, ensuring its output format correctly
        respects the POINT_PRECISION_DECIMALS constant.
        """
        assert repr(p) == expected_repr

    # --- Equality Tests (`__eq__`) ---
    @pytest.mark.parametrize("p1, p2, expected", EQUALITY_TEST_CASES)
    def test_equality(self, p1, p2, expected):
        """
        Tests the rounding-based __eq__ method using a dynamically generated
        set of edge cases that respect POINT_PRECISION_DECIMALS.
        """
        assert (p1 == p2) == expected

    @pytest.mark.parametrize("p1, p2, should_match", HASH_TEST_CASES)
    def test_hash(self, p1, p2, should_match):
        """
        Tests the __hash__ method using a dynamically generated set of edge
        cases that respect POINT_PRECISION_DECIMALS. It also verifies that
        the hash-equals contract is maintained.
        """
        if should_match:
            assert hash(p1) == hash(p2)
        else:
            # For these well-defined, non-colliding cases, hashes should not match.
            assert hash(p1) != hash(p2)

        # Always verify the fundamental contract: if points are equal, their hashes MUST be equal.
        # This is the most important assertion in this test.
        if p1 == p2:
            assert hash(p1) == hash(p2), "FAIL: Points that are equal must have the same hash."

    # --- Vector Arithmetic Tests ---
    def test_subtraction(self):
        """Tests vector subtraction (p1 - p2)."""
        assert P_5_10 - P_1_3 == Point(4, 7)

    def test_addition(self):
        """Tests vector addition (p1 + p2)."""
        assert P_5_10 + P_1_NEG3 == Point(6, 7)

    def test_multiplication(self):
        """Tests scalar multiplication (p * scalar)."""
        assert P_2_NEG3 * 3 == Point(6, -9)
        assert P_2_NEG3 * -1.5 == Point(-3, 4.5)


# ======================================
# --- Tests for euclidean_dist function ---
# ======================================

@pytest.mark.parametrize("p1, p2, expected_dist", [
    pytest.param(P_0_0, P_3_4, 5.0, id="3-4-5-triangle"),
    pytest.param(P_3_4, P_0_0, 5.0, id="order-independent"),
    pytest.param(P_5_5, Point(5, 5), 0.0, id="zero-distance"),
    pytest.param(P_NEG1_0, P_2_0, 3.0, id="horizontal-distance"),
    pytest.param(Point(0, -1), Point(0, 2), 3.0, id="vertical-distance"),
    pytest.param(P_0_0, P_1_1, math.sqrt(2), id="diagonal-distance-sqrt2"),
    pytest.param(P_NEG1_NEG1, P_1_1, math.sqrt(8), id="diagonal-across-origin"),
])
def test_euclidean_dist(p1, p2, expected_dist):
    """Tests the euclidean_dist function with various points."""
    assert euclidean_dist(p1, p2) == pytest.approx(expected_dist)


class TestPointImplementation:
    """
    Tests the internal consistency of the Point class, ensuring the
    hashing and equality logic are perfectly synchronized.
    """

    def test_points_across_hash_boundary_are_not_equal(self):
        """
        Validates that two points on opposite sides of a rounding boundary
        are correctly identified as NOT equal. This confirms that `__eq__`
        is using the same rounding logic as `__hash__`.
        """
        # The rounding boundary is at 0.5 * 10**(-D)
        boundary = 0.5 * (10 ** -POINT_PRECISION_DECIMALS)

        # Create two points that straddle this boundary.
        # Pick a tiny delta that doesn't affect the rounding itself.
        tiny_delta = 10 ** -(POINT_PRECISION_DECIMALS + 3)

        p1 = Point(boundary - tiny_delta, 0)
        p2 = Point(boundary + tiny_delta, 0)

        # 1. Verify they fall into different hash buckets as expected.
        assert hash(p1) != hash(p2), "Test setup failed: points should have different hashes."

        # 2. THE CRITICAL ASSERTION for the NEW implementation:
        # Because they have different hashes, they MUST NOT be equal.
        # This test will now pass with the corrected Point class. It serves as a
        # crucial regression test against re-introducing `isclose` into `__eq__`.
        assert p1 != p2, (
            "FATAL: Point hash/equals contract is BROKEN. "
            "Points with different hashes are considered equal."
        )

    def test_close_points_within_same_hash_bucket_are_equal(self):
        """
        Validates the "good case": two points that are very close and fall
        in the same hash bucket should be equal.
        """
        # A base point far from any rounding boundary
        base_x = 0.123

        # A tiny delta
        delta = 10 ** -(POINT_PRECISION_DECIMALS + 3)

        p1 = Point(base_x, 0)
        p2 = Point(base_x + delta, 0)

        # 1. They should have the same hash because they don't cross a boundary.
        assert hash(p1) == hash(p2)

        # 2. They should be considered equal.
        assert p1 == p2
