import argparse
import platform
import time

import numpy as np

from make_planes import random_planes, rotating_planes
from slicing import extract_slice


def four_points(points):
    if len(points) == 3:
        return [points[0], points[0], points[1], points[2]]
    return points


def measure(volume, planes):
    # Cuts per second, only the computation (no file reading, no video).
    start = time.perf_counter()
    for points in planes:
        extract_slice(volume, *four_points(points))
    return len(planes) / (time.perf_counter() - start)


def main():
    parser = argparse.ArgumentParser(description="Measure how many cuts per second slicing.py computes.")
    parser.add_argument("--size", type=int, default=500, help="the volume is size^3 bytes (default 500)")
    parser.add_argument("--count", type=int, default=200, help="number of cuts per test (default 200)")
    args = parser.parse_args()

    # Random bytes, stored with x first like a volume read from a NRRD file.
    shape = (args.size, args.size, args.size)
    rng = np.random.default_rng(0)
    volume = np.asfortranarray(rng.integers(0, 256, shape, dtype=np.uint8))
    print(f"Volume {shape} uint8, {platform.processor() or platform.machine()}, Python {platform.python_version()}")

    tests = [
        ("big squares turning around the center (worst case)", rotating_planes(shape, args.count, 1)),
        ("random triangles and trapezoids", random_planes(shape, args.count, 0)),
    ]
    for name, planes in tests:
        extract_slice(volume, *four_points(planes[0]))  # first call not counted
        print(f"{name}: {measure(volume, planes):.1f} cuts per second")


if __name__ == "__main__":
    main()
