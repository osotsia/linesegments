# Main.py
import math

from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize, unary_union

from geoprocessor import find_all_vertices_and_segment_map, build_graph, find_face_perimeters, bcolors


def shapeley_perimeter_product(list_of_segments):
    """
    Reference implementation using shapely
    """
    lines = [LineString(s) for s in list_of_segments]

    # Create a single geometry object
    union_of_lines = unary_union(MultiLineString(lines))

    perimeters_product = 1.0
    found_polygons = False

    # iterate over all minimal polygons
    for poly in polygonize(union_of_lines):
        perimeters_product *= poly.length
        found_polygons = True

    if not found_polygons:
        perimeters_product = None

    return perimeters_product


# ------------------------------------------------------------------------------------
# TESTS


square_segments = (
    ((1, 1), (1, 2)),
    ((1, 2), (2, 2)),
    ((2, 2), (2, 1)),
    ((2, 1), (1, 1))
)
hourglass_segments = (
    ((1, 1), (1, 2)),
    ((1, 2), (2, 1)),
    ((2, 1), (2, 2)),
    ((2, 2), (1, 1))
)
window_segments = (
    ((1, 1), (1, 2)),
    ((1, 2), (2, 2)),
    ((2, 2), (2, 1)),
    ((2, 1), (1, 1)),
    ((1.5, 1), (1.5, 2)),
    ((1, 1.5), (2, 1.5))
)
final_shape_segments = (
    ((1, 1), (1, 2)),
    ((1, 2), (1.8, 2)),
    ((1.8, 2), (1.8, 1)),
    ((1.8, 1), (1, 1)),
    ((1.2, 1), (1.2, 2)),
    ((1.6, 1), (1.6, 2)),
    ((1, 1.5), (1.6, 1.8)),
    ((1, 1.3), (1.8, 1.7)),
    ((1.2, 1.2), (1.8, 1.5))
)
hourglass_modded_segments = (
    ((1, 2), (2, 2)),
    ((1, 1), (2, 1)),
    ((1, 1), (1, 2)),
    ((1, 2), (2, 1)),
    ((2, 1), (2, 2)),
    ((2, 2), (1, 1))
)


def run_end_to_end_pipeline():
    suite_name = "end_to_end_pipeline"
    print(f"Testing {suite_name}...")
    passed_count = 0
    failed_count = 0

    test_cases = [
        {
            "name": "Square",
            "structure": square_segments,
            "expected_product": shapeley_perimeter_product(square_segments)
        },
        {
            "name": "Hourglass",
            "structure": hourglass_segments,
            "expected_product": shapeley_perimeter_product(hourglass_segments)
        },
        {
            "name": "Window",
            "structure": window_segments,
            "expected_product": shapeley_perimeter_product(window_segments)
        },
        {
            "name": "Final Shape",
            "structure": final_shape_segments,
            "expected_product": shapeley_perimeter_product(final_shape_segments)
        },
        {
            "name": "Hourglass Modded",
            "structure": hourglass_modded_segments,
            "expected_product": shapeley_perimeter_product(hourglass_modded_segments)-1
        }
    ]

    for case in test_cases:
        test_name = case["name"]
        structure = case["structure"]
        expected_product = case["expected_product"]

        try:
            # Step 1: Find all vertices
            segment_to_points_map, all_vertices_set, point_cache = find_all_vertices_and_segment_map(structure)
            # Step 2: Construct planar graph
            planar_graph = build_graph(segment_to_points_map, all_vertices_set, point_cache)
            # Step 3: Find face perimeters and calculate perimeter product
            list_of_perimeters = find_face_perimeters(planar_graph)
            actual_product = math.prod(list_of_perimeters)

            # Compare the actual result with the expected result
            is_pass = math.isclose(actual_product, expected_product, rel_tol=1e-4, abs_tol=1e-4)

            if is_pass:
                print(f"  - Test '{test_name}': {bcolors.OKGREEN}PASSED{bcolors.ENDC}")
                passed_count += 1
            else:
                print(f"  - Test '{test_name}': {bcolors.FAIL}FAILED{bcolors.ENDC}")
                print(f"    - Actual product:   {actual_product:.7f}")
                print(f"    - Expected product: {expected_product:.7f}")
                print("    - Debug Info:")
                print(f"      - Vertices Found: {len(all_vertices_set)}")
                print(f"      - Faces Found:    {len(list_of_perimeters)}")
                print(f"      - Perimeters:     {sorted(list_of_perimeters)}")
                failed_count += 1

        except Exception as e:
            print(f"  - Test '{test_name}': {bcolors.FAIL}FAILED{bcolors.ENDC} (Exception)")
            print(f"    - Error: {e}")
            failed_count += 1

    # --- Final Summary ---
    print(f"\n{suite_name} tests finished: {passed_count} passed, {failed_count} failed.")

    return failed_count == 0


if __name__ == "__main__":

    if not run_end_to_end_pipeline():
        print(f"Some pipeline tests {bcolors.FAIL}FAILED{bcolors.ENDC}.")
    else:
        print(f"All pipeline tests {bcolors.OKGREEN}PASSED{bcolors.ENDC} successfully!")
