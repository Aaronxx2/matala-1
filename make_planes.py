import argparse
import csv
from pathlib import Path

import nrrd
import numpy as np

HEADER = ["Number of Points (3 or 4)", "x1", "y1", "z1", "x2", "y2", "z2",
          "x3", "y3", "z3", "x4", "y4", "z4"]


def rotating_planes(shape, count, axis):
    # Makes `count` rectangles (trapezoids with equal bases) that turn around
    # the center of the volume, around the given axis, like a page of a book.
    # Returns a list of 4 points (a1, a2, b, c) for each plane.
    shape = np.array(shape, dtype=float)
    center = (shape - 1) / 2  # voxel indices go from 0 to size - 1

    # w = the rotation axis, it stays in every plane.
    w = np.zeros(3)
    w[axis] = 1
    others = [i for i in range(3) if i != axis]

    # Half height: the volume along the axis.
    # Half width: half of the diagonal of the 2 other sizes, so the plane covers
    # the whole volume at every angle (the parts outside are black).
    half_height = (shape[axis] - 1) / 2
    half_width = np.linalg.norm(shape[others] - 1) / 2

    planes = []
    for i in range(count):
        # 0 to 180 degrees is enough: at 180 the plane is the same as at 0.
        angle = np.pi * i / count
        u = np.zeros(3)
        u[others[0]] = np.cos(angle)
        u[others[1]] = np.sin(angle)

        # Top base a1 -> a2, bottom base b -> c, sides a1 -> b and a2 -> c.
        # The top of the image is at index 0 of the axis (top of the head in MRHead).
        a1 = center - half_height * w - half_width * u
        a2 = center - half_height * w + half_width * u
        b = center + half_height * w - half_width * u
        c = center + half_height * w + half_width * u
        planes.append([a1, a2, b, c])
    return planes


def random_planes(shape, count, seed):
    # Makes `count` random triangles and trapezoids, in any direction, like the
    # professor's CSV. Some points can be outside the volume (that part is black).
    # Every shape is valid: equal sides, small base <= big base, all on one plane.
    rng = np.random.default_rng(seed)  # same seed = same CSV every time
    shape = np.array(shape, dtype=float)
    biggest = shape.max()

    planes = []
    for i in range(count):
        # d = from a towards the big base, e = along the bases, d and e are perpendicular.
        d = rng.normal(size=3)
        d = d / np.linalg.norm(d)
        e = np.cross(d, rng.normal(size=3))
        e = e / np.linalg.norm(e)

        length = rng.uniform(0.3, 0.9) * biggest  # distance from a to the big base
        half_base = rng.uniform(0.15, 0.6) * biggest  # half of the big base

        # The middle of the shape is somewhere in the middle half of the volume,
        # so most of the cut shows the head. The corners can still be outside.
        middle = rng.uniform(0.25, 0.75, 3) * (shape - 1)
        a = middle - length / 2 * d  # top point (or middle of the small base)
        b = a + length * d - half_base * e
        c = a + length * d + half_base * e

        if rng.random() < 0.5:
            # Triangle: a -> b and a -> c have the same length because b and c
            # are symmetric around the line from a in direction d.
            planes.append([a, b, c])
        else:
            # Trapezoid: small base a1 a2, also symmetric, and smaller than b c.
            half_small = rng.uniform(0.1, 0.9) * half_base
            a1 = a - half_small * e
            a2 = a + half_small * e
            planes.append([a1, a2, b, c])
    return planes


def main():
    parser = argparse.ArgumentParser(description="Write a CSV of planes for a volume (turning around the center, or random).")
    parser.add_argument("nrrd_file", type=Path)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--count", type=int, default=100, help="number of planes (default 100)")
    parser.add_argument("--axis", type=int, default=1, choices=[0, 1, 2],
                        help="rotation axis (default 1, the top-bottom axis of MRHead)")
    parser.add_argument("--mode", choices=["rotate", "random"], default="rotate",
                        help="rotate: planes turning around the center, random: random triangles and trapezoids")
    parser.add_argument("--seed", type=int, default=0, help="random seed for --mode random (default 0)")
    args = parser.parse_args()

    # Only the header is needed to know the size of the volume.
    header = nrrd.read_header(str(args.nrrd_file))
    shape = [int(s) for s in header["sizes"]]
    print(f"Volume shape: {tuple(shape)}")

    if args.mode == "rotate":
        planes = rotating_planes(shape, args.count, args.axis)
    else:
        planes = random_planes(shape, args.count, args.seed)
    with args.csv_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(HEADER)
        for points in planes:
            # 6 decimals so the side lengths stay equal within EPS.
            row = [len(points)] + [f"{value:.6f}" for point in points for value in point]
            # A triangle has 3 points: the last 3 cells stay empty.
            row += [""] * (len(HEADER) - len(row))
            writer.writerow(row)
    print(f"Saved {len(planes)} planes: {args.csv_file.resolve()}")


if __name__ == "__main__":
    main()
