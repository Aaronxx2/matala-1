# The demo program: python Ex0.py file.nrrd file.csv file.mp4
# These tests write real NRRD, CSV and MP4 files in a temporary folder.

import imageio.v2 as imageio
import nrrd
import numpy as np
import pytest

import Ex0

HEADER = "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"


def write_files(tmp_path, rows, dtype=np.uint8):
    volume = (np.arange(16 * 16 * 16) % 200 + 1).astype(dtype).reshape((16, 16, 16), order="F")
    nrrd_path = tmp_path / "volume.nrrd"
    nrrd.write(str(nrrd_path), volume, index_order="F")
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text(HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")
    return volume, nrrd_path, csv_path


def count_frames(mp4_path):
    with imageio.get_reader(mp4_path) as video:
        return sum(1 for frame in video)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
def test_nrrd_types_are_read_with_x_first(tmp_path, dtype):
    # Write a real NRRD file of each type and read it back.
    volume = np.zeros((6, 7, 8), dtype=dtype)
    volume[1, 2, 3] = np.iinfo(dtype).max  # different sizes: a wrong axis order would show
    path = tmp_path / "v.nrrd"
    nrrd.write(str(path), volume, index_order="F")
    loaded = Ex0.load_volume(path)
    assert loaded.shape == (6, 7, 8)
    assert loaded.dtype == dtype
    assert loaded[1, 2, 3] == np.iinfo(dtype).max


def test_missing_file_gives_an_error(tmp_path):
    with pytest.raises(OSError):
        Ex0.main([str(tmp_path / "missing.nrrd"), str(tmp_path / "planes.csv"), str(tmp_path / "out.mp4")])


def test_one_frame_per_row(tmp_path):
    rows = ["3,8,2,8,2,13,8,14,13,8,,,", "4,2,2,8,13,2,8,2,13,8,13,13,8", "3,8,2,8,2,13,8,14,13,8,,,"]
    volume, nrrd_path, csv_path = write_files(tmp_path, rows)
    mp4_path = tmp_path / "out.mp4"
    Ex0.main([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert count_frames(mp4_path) == 3


def test_bad_row_leaves_no_video(tmp_path):
    # Row 3 is not isosceles: error with the row number, and no video file at all.
    rows = ["3,8,2,8,2,13,8,14,13,8,,,", "3,0,0,0,10,0,0,0,12,0,,,"]
    volume, nrrd_path, csv_path = write_files(tmp_path, rows)
    mp4_path = tmp_path / "out.mp4"
    with pytest.raises(ValueError, match="CSV row 3"):
        Ex0.main([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert not mp4_path.exists()
    assert list(tmp_path.glob("*.mp4")) == []


def test_bad_row_keeps_an_old_video(tmp_path):
    # An old file with the same name is not replaced by a broken one.
    rows = ["3,0,0,0,10,0,0,0,12,0,,,"]
    volume, nrrd_path, csv_path = write_files(tmp_path, rows)
    mp4_path = tmp_path / "out.mp4"
    mp4_path.write_bytes(b"old video")
    with pytest.raises(ValueError):
        Ex0.main([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert mp4_path.read_bytes() == b"old video"


def test_same_value_same_gray_in_every_frame():
    # The gray scale comes from the volume, not from each image (FR-9):
    # 100 is the same gray in an image with values up to 200 and in one with only 100.
    bright = Ex0.to_frame(np.array([[100, 200]], dtype=np.uint16), 0, 200, 16, 16)
    dark = Ex0.to_frame(np.array([[100, 100]], dtype=np.uint16), 0, 200, 16, 16)
    assert bright.dtype == np.uint8
    assert bright[7, 7] == dark[7, 7] == 127  # 100 / 200 * 255
    assert bright[7, 8] == 255


def test_small_image_is_in_the_middle_of_a_black_frame():
    # Every frame has the same size, the image is centered on black (FR-10).
    frame = Ex0.to_frame(np.full((2, 4), 50, dtype=np.uint8), 0, 50, 16, 16)
    assert frame.shape == (16, 16)
    assert np.all(frame[7:9, 6:10] == 255)
    assert np.count_nonzero(frame) == 8
