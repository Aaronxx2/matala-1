import argparse
import csv
import os
import sys
import time
from pathlib import Path

import imageio.v2 as imageio
import nrrd
import numpy as np

from slicing import check_shape, extract_slice, four_points, image_size


def load_volume(nrrd_path):
    # Keep the NRRD axis order so points are used as voxel indices (x, y, z).
    volume, header = nrrd.read(str(nrrd_path), index_order="F")
    if volume.ndim != 3:
        raise ValueError(f"{nrrd_path}: expected a 3D volume, got {volume.ndim} dimensions.")
    return volume


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


def check_planes(planes):
    # Checks every plane and returns the (height, width) of each image, in the CSV order.
    sizes = []
    for row_number, points in planes:
        try:
            a1, a2, b, c, dab, dbc = check_shape(*four_points(points))
        except ValueError as error:
            raise ValueError(f"CSV row {row_number}: {error}")
        sizes.append(image_size(dab, dbc))
    return sizes


def to_frame(image, low, high, frame_height, frame_width):
    # Gray scale from low (black) to high (white), image in the middle of a black frame.
    pixels = np.clip((image - low) / (high - low) * 255, 0, 255).astype(np.uint8)
    frame = np.zeros((frame_height, frame_width), dtype=np.uint8)
    top = (frame_height - pixels.shape[0]) // 2
    left = (frame_width - pixels.shape[1]) // 2
    frame[top:top + pixels.shape[0], left:left + pixels.shape[1]] = pixels
    return frame


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cut a 3D volume along each plane of a CSV file and save the cuts as a video.")
    parser.add_argument("nrrd_file", type=Path)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("mp4_file", type=Path)
    parser.add_argument("--fps", type=int, default=10, help="frames per second of the video (default 10)")
    args = parser.parse_args(argv)

    volume = load_volume(args.nrrd_file)
    print(f"Volume shape: {volume.shape}")
    planes = read_planes(args.csv_file)

    # Check every plane before writing anything, and get the size of each image.
    sizes = check_planes(planes)

    # Same gray scale for every frame: 0 is black and the max of the volume is white.
    # So the same value always has the same brightness in the whole video.
    low = min(0, float(volume.min()))
    high = float(volume.max())
    if high <= low:
        high = low + 1

    # All frames of a video must have the same size: take the biggest image,
    # the smaller ones are put in the middle on a black background.
    # Multiple of 16 because video encoders work with blocks of 16 pixels.
    frame_height = int(np.ceil(max(h for h, w in sizes) / 16)) * 16
    frame_width = int(np.ceil(max(w for h, w in sizes) / 16)) * 16

    # Write in a temporary file first, so an error never leaves a half video.
    temp_file = args.mp4_file.with_name(args.mp4_file.stem + ".tmp.mp4")
    cut_time = 0  # time spent computing the cuts only, without the video
    try:
        with imageio.get_writer(temp_file, fps=args.fps) as video:
            for row_number, points in planes:
                start = time.perf_counter()
                image = extract_slice(volume, *four_points(points))
                cut_time += time.perf_counter() - start

                video.append_data(to_frame(image, low, high, frame_height, frame_width))
        os.replace(temp_file, args.mp4_file)
    except BaseException:
        if temp_file.exists():
            temp_file.unlink()
        raise

    print(f"Saved video: {args.mp4_file.resolve()} ({len(planes)} frames)")
    speed = len(planes) / cut_time if cut_time > 0 else float("inf")
    print(f"Cuts computed in {cut_time:.2f} s: {speed:.1f} cuts per second (video writing not counted)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        # Show a short message instead of a Python traceback.
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
