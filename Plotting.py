import matplotlib.pyplot as plt
import math


def plot_segments(segments, padding_factor=0.1, show_points=True):
    """
    Plots a shape defined by a list of line segments.

    Args:
        segments (list): A list of line segments. Each segment should be a list
                         containing two points, where each point is a list or
                         tuple of two numbers (x, y).
                         Example: [[[x1, y1], [x2, y2]], [[x3, y3], [x4, y4]], ...]
        padding_factor (float): A factor to add padding around the calculated bounds.
                                0.1 means 10% padding based on the range.
        show_points (bool): If True, adds markers at the endpoints of each segment.
    """
    if not segments:
        print("Warning: No segments provided to plot.")
        # Plot an empty graph if no segments are given
        fig, ax = plt.subplots()
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title("Plotted Line Segments (No Data)")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.grid(True)
        plt.show()
        return

    # --- 1. Calculate Bounds ---
    min_x, max_x = math.inf, -math.inf
    min_y, max_y = math.inf, -math.inf
    valid_points_found = False

    for segment in segments:
        # Basic validation for segment structure
        if not isinstance(segment, (list, tuple)) or len(segment) != 2:
            print(f"Warning: Skipping invalid segment format: {segment}")
            continue
        p1, p2 = segment
        # Basic validation for point structure
        if not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in [p1, p2]):
            print(f"Warning: Skipping segment with invalid point format: {segment}")
            continue
        if not all(isinstance(coord, (int, float)) for p in [p1, p2] for coord in p):
            print(f"Warning: Skipping segment with non-numeric coordinates: {segment}")
            continue

        valid_points_found = True  # Mark that we found at least one valid segment
        # Update bounds based on both points in the segment
        for x, y in [p1, p2]:
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

    if not valid_points_found:
        print("Warning: No valid segments found to plot.")
        # Plot an empty graph similar to the no segments case
        fig, ax = plt.subplots()
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title("Plotted Line Segments (No Valid Data)")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.grid(True)
        plt.show()
        return

    # --- 2. Create Plot ---
    fig, ax = plt.subplots()

    # --- 3. Plot Segments ---
    marker_style = 'o' if show_points else None
    for segment in segments:
        # Minimal re-validation just to be safe before unpacking
        if isinstance(segment, (list, tuple)) and len(segment) == 2:
            p1, p2 = segment
            if all(isinstance(p, (list, tuple)) and len(p) == 2 for p in [p1, p2]):
                if all(isinstance(coord, (int, float)) for p in [p1, p2] for coord in p):
                    # Plot the line segment
                    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                            marker=marker_style, linestyle='-', color='blue')

    # --- 4. Set Bounds with Padding ---
    range_x = max_x - min_x
    range_y = max_y - min_y

    # Handle cases where all points lie on a vertical or horizontal line (or it's a single point)
    # Add a minimal absolute padding if range is zero, otherwise use relative padding
    pad_x = padding_factor * range_x if range_x > 1e-6 else 0.5  # Use 0.5 absolute padding if range is effectively zero
    pad_y = padding_factor * range_y if range_y > 1e-6 else 0.5  # Use 0.5 absolute padding if range is effectively zero

    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)

    # --- 5. Customize Appearance ---
    ax.set_aspect('equal', adjustable='box')  # Crucial for correct shape proportions
    ax.set_title("Plotted Line Segments")
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.grid(True)  # Add a grid for better readability

    # --- 6. Show Plot ---
    plt.show()


# --- Example Usage ---
'''
# 1. Your Square Example
square = [
    [[1, 1], [1, 2]],
    [[1, 2], [2, 2]],
    [[2, 2], [2, 1]],
    [[2, 1], [1, 1]]
]
print("Plotting square...")
plot_segments(square)

# 2. A Triangle Example
triangle = [
    [[0, 0], [5, 0]],
    [[5, 0], [2.5, 4]],
    [[2.5, 4], [0, 0]]
]
print("\nPlotting triangle...")
plot_segments(triangle, show_points=True) # Show endpoints explicitly

# 3. Disconnected Segments Example
disconnected = [
    [[-1, -1], [-2, -2]], # Segment 1
    [[1, 2], [3, 1]],     # Segment 2
    [[0, 3], [0, 1]]      # Segment 3 (vertical)
]
print("\nPlotting disconnected segments...")
plot_segments(disconnected, padding_factor=0.2) # More padding

# 4. Single Point (represented as a zero-length segment)
# Note: matplotlib might not display a zero-length line well,
# but `show_points=True` makes the point visible.
single_point_segment = [ [[3, 3], [3, 3]] ]
print("\nPlotting single point segment...")
plot_segments(single_point_segment, show_points=True)

# 5. Empty list example
print("\nPlotting empty list...")
plot_segments([])

# 6. Example with some invalid data mixed in
mixed_data = [
    [[1,1], [2,2]],
    "not a segment",       # Invalid format
    [[3,3], [4,4,4]],      # Invalid point format
    [[5,5], [6,6]],
    [[7, 'a'], [8, 8]]     # Non-numeric coordinate
]
print("\nPlotting mixed valid/invalid data...")
plot_segments(mixed_data)
'''

final_shape_segments = [
    [[1, 1], [1, 2]],
    [[1, 2], [1.8, 2]],
    [[1.8, 2], [1.8, 1]],
    [[1.8, 1], [1, 1]],
    [[1.2, 1], [1.2, 2]],
    [[1.6, 1], [1.6, 2]],
    [[1, 1.5], [1.6, 1.8]],
    [[1, 1.3], [1.8, 1.7]],
    [[1.2, 1.2], [1.8, 1.5]]
]

# plot_segments(final_shape_segments)


segments_coords_castle = [
    # Outer rectangle (perimeter = 2*(6+4) = 20)
    [[0, 0], [6, 0]],
    [[6, 0], [6, 4]],
    [[6, 4], [0, 4]],
    [[0, 4], [0, 0]],

    # Inner cutout rectangle (perimeter = 2*(2+1) = 6)
    # This cutout will define an area *around* it within the larger rectangle.
    [[1, 1], [3, 1]],
    [[3, 1], [3, 2]],
    [[3, 2], [1, 2]],
    [[1, 2], [1, 1]],

    # Attached structure (a 2x2 square, perimeter = 8)
    # It shares the edge [[2,4], [4,4]] with the top of the outer rectangle.
    [[2, 4], [4, 4]],  # This edge is part of the outer rectangle too
    [[4, 4], [4, 6]],
    [[4, 6], [2, 6]],
    [[2, 6], [2, 4]],
]

plot_segments(segments_coords_castle)
