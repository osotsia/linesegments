
This project implements a computational geometry engine that processes 2D line segments to find all minimal enclosed polygons (faces) and calculate the product of their perimeters. The pipeline identifies all segment endpoints and intersections to form vertices, constructs a planar graph, and uses a traversal algorithm to trace the minimal faces. The implementation includes robust handling of floating-point inaccuracies.

## Features

-   Constructs a planar graph from 2D line segments, handling all intersections.
-   Detects all minimal enclosed polygonal faces using a "right-hand rule" traversal.
-   Manages floating-point precision with a custom `Point` class.
-   Includes a Matplotlib-based utility for visualizing segment data.
-   Validated with a comprehensive `pytest` test suite.

## FAQ

**Q: What is a "minimal face"?**

A: It is an enclosed region that cannot be further subdivided by any other line segments in the input. For instance, a window pane shape results in four small square faces, not one large outer rectangle.

**Q: Why is a custom `Point` class used?**

A: To handle floating-point imprecision. It ensures that geometrically identical points are treated as a single vertex, which is critical for building a correct graph representation from the input segments.

**Q: How is the output validated?**

A: The `Main.py` script compares the calculated perimeter product against a reference result generated using the `shapely` library's polygonization functions.