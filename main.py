import argparse
import csv
from pathlib import Path

import nrrd
import numpy as np
from PIL import Image

from slicing import extract_slice, extract_triangle_slice


def main():
    project_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Save the first supported triangle slice as a PNG image.")
    parser.add_argument("nrrd_file", nargs="?", type=Path, default=project_dir / "MRHead_1.nrrd")
    parser.add_argument("csv_file", nargs="?", type=Path, default=project_dir / "points.csv")
    parser.add_argument("output_file", nargs="?", type=Path, default=project_dir / "slice.png")
    args = parser.parse_args()

    # Keep the NRRD axis order so points are used as voxel indices (x, y, z).
    volume, header = nrrd.read(str(args.nrrd_file), index_order="F")
    print(f"Volume shape: {volume.shape}")

    slices = []
    with args.csv_file.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            point_count = int(row["Number of Points (3 or 4)"])
            if point_count not in (3, 4):
                raise ValueError(f"CSV row {row_number}: expected 3 or 4 points.")

            p1 = [float(row["x1"]), float(row["y1"]), float(row["z1"])]
            p2 = [float(row["x2"]), float(row["y2"]), float(row["z2"])]
            p3 = [float(row["x3"]), float(row["y3"]), float(row["z3"])]

            if point_count == 3:
                # Triangle: a = p1, b = p2, c = p3.
                image = extract_triangle_slice(volume, p1, p2, p3)
            else:
                p4 = [float(row["x4"]), float(row["y4"]), float(row["z4"])]
                # Trapezoid: a1 = p1, a2 = p2, b = p3, c = p4.
                image = extract_slice(volume, p1, p2, p3, p4)
            # Scale the sampled values to grayscale pixels from 0 to 255.
            minimum = image.min()
            maximum = image.max()
            pixels = np.zeros(image.shape, dtype=np.uint8)
            if maximum > minimum:
                pixels = ((image - minimum) / (maximum - minimum) * 255).astype(np.uint8)
            Image.fromarray(pixels).save(args.output_file, format="PNG")
            print(f"CSV row {row_number}: extracted image with shape {image.shape}")
            print(f"Saved image: {args.output_file.resolve()}")
            return image

    if not slices:
        raise ValueError("The CSV file contains no supported slices.")
    return slices


if __name__ == "__main__":
    main()
