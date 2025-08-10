# geoprocessor/primitives.py
import math

# Epsilon for geometric calculations (e.g., is a point ON a line).
GEOMETRIC_TOLERANCE = 1e-9

# Number of decimal places to round to for both hashing and equality.
POINT_PRECISION_DECIMALS = 7


# 0. Utilities / Preliminaries

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Point:
    """
    Represents a 2D point with x and y coordinates.
    Includes methods for equality and hashing that account for
    floating-point precision issues.
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        # Represent with a reasonable number of decimal places for display
        return f"Point({self.x:.{POINT_PRECISION_DECIMALS + 1}f}, {self.y:.{POINT_PRECISION_DECIMALS + 1}f})"

    def __eq__(self, other):
        """
        Two points are equal if their coordinates are identical after
        rounding to POINT_PRECISION_DECIMALS.
        """
        if not isinstance(other, Point):
            return NotImplemented
        # Equality logic now matches hashing logic.
        return (round(self.x, POINT_PRECISION_DECIMALS) == round(other.x, POINT_PRECISION_DECIMALS) and
                round(self.y, POINT_PRECISION_DECIMALS) == round(other.y, POINT_PRECISION_DECIMALS))

    def __hash__(self):
        # Hash based on coordinates rounded to a fixed number of decimal places
        # to ensure points that are "close enough" (and thus considered equal by __eq__)
        # hash to the same value.
        return hash((round(self.x, POINT_PRECISION_DECIMALS),
                     round(self.y, POINT_PRECISION_DECIMALS)))

    def __sub__(self, other):
        """p1 - p2 -> returns a new Point representing the vector."""
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """p1 + vec -> returns a new Point."""
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        """vec * scalar -> returns a scaled vector."""
        return Point(self.x * scalar, self.y * scalar)

    # Optional: A tuple representation for easier use in some contexts
    def as_tuple(self):
        return (self.x, self.y)


def euclidean_dist(point1, point2):
    """Takes Point objects, calculates Euclidean distance"""
    return math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2)
