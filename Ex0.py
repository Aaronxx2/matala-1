import argparse
import csv
import os
import sys
from pathlib import Path

import imageio.v2 as imageio
import nrrd
import numpy as np

from slicing import extract_slice


def read_planes(csv_path):
    # Returns a list of (row_number, points), one item per CSV row, in the CSV order.
    # 3 points = triangle (a, b, c), 4 points = trapezoid (a1, a2, b, c).
    planes = []
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            try:
                point_count = int(row["Number of Points (3 or 4)"])
                if point_count not in (3, 4):
                    raise ValueError("expected 3 or 4 points")
                points = []
                for i in range(1, point_count + 1):
                    point = [float(row[f"x{i}"]), float(row[f"y{i}"]), float(row[f"z{i}"])]
                    points.append(point)
            except (ValueError, TypeError, KeyError) as error:
                # Empty cell, text instead of a number, missing column...
                raise ValueError(f"CSV row {row_number}: invalid row ({error}).")
            if not np.all(np.isfinite(points)):
                raise ValueError(f"CSV row {row_number}: nan or inf is not a valid coordinate.")
            planes.append((row_number, points))
    if not planes:
        raise ValueError("The CSV file contains no planes.")
    return planes


def cut(volume, row_number, points):
    # Cuts one plane, the triangle is a trapezoid where a1 = a2 = a.
    if len(points) == 3:
        a1, a2, b, c = points[0], points[0], points[1], points[2]
    else:
        a1, a2, b, c = points
    try:
        return extract_slice(volume, a1, a2, b, c)
    except ValueError as error:
        raise ValueError(f"CSV row {row_number}: {error}")


def image_size(points):
    # Size of the image E without computing it (same formulas as in slicing.py).
    a1 = np.array(points[0], dtype=float)
    b = np.array(points[-2], dtype=float)
    c = np.array(points[-1], dtype=float)
    height = int(np.ceil(np.linalg.norm(b - a1)))
    width = int(np.floor(np.linalg.norm(c - b))) + 1
    return height, width


def main():
    parser = argparse.ArgumentParser(description="Cut a 3D volume along each plane of a CSV file and save the cuts as a video.")
    parser.add_argument("nrrd_file", type=Path)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("mp4_file", type=Path)
    parser.add_argument("--fps", type=int, default=10, help="frames per second of the video (default 10)")
    args = parser.parse_args()

    # Keep the NRRD axis order so points are used as voxel indices (x, y, z).
    volume, header = nrrd.read(str(args.nrrd_file), index_order="F")
    print(f"Volume shape: {volume.shape}")
    planes = read_planes(args.csv_file)

    # Same gray scale for every frame: 0 is black and the max of the volume is white.
    # So the same value always has the same brightness in the whole video.
    low = min(0, float(volume.min()))
    high = float(volume.max())
    if high <= low:
        high = low + 1

    # All frames of a video must have the same size: take the biggest image,
    # the smaller ones are put in the middle on a black background.
    # Multiple of 16 because video encoders work with blocks of 16 pixels.
    sizes = [image_size(points) for row_number, points in planes]
    frame_height = int(np.ceil(max(h for h, w in sizes) / 16)) * 16
    frame_width = int(np.ceil(max(w for h, w in sizes) / 16)) * 16

    # Write in a temporary file first, so a bad row never leaves a half video.
    temp_file = args.mp4_file.with_name(args.mp4_file.stem + ".tmp.mp4")
    try:
        with imageio.get_writer(temp_file, fps=args.fps) as video:
            for row_number, points in planes:
                image = cut(volume, row_number, points)
                pixels = np.clip((image - low) / (high - low) * 255, 0, 255).astype(np.uint8)

                frame = np.zeros((frame_height, frame_width), dtype=np.uint8)
                top = (frame_height - pixels.shape[0]) // 2
                left = (frame_width - pixels.shape[1]) // 2
                frame[top:top + pixels.shape[0], left:left + pixels.shape[1]] = pixels
                video.append_data(frame)
                print(f"CSV row {row_number}: frame with image shape {image.shape}")
        os.replace(temp_file, args.mp4_file)
    except Exception:
        if temp_file.exists():
            temp_file.unlink()
        raise

    print(f"Saved video: {args.mp4_file.resolve()} ({len(planes)} frames)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        # Show a short message instead of a Python traceback.
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
