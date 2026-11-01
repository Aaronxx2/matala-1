# Strange inputs: the program must stop with a clear message, never crash
# with a Python error or give a wrong image without saying anything.

import numpy as np
import pytest

from Ex0 import read_planes
from slicing import extract_slice

VOLUME = np.full((20, 20, 20), 100, dtype=np.uint8)
HEADER = "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"


# ---- Shapes ----

@pytest.mark.parametrize("a1, a2, b, c, message", [
    # same point three times: no side, division by zero
    ([5, 5, 5], [5, 5, 5], [5, 5, 5], [5, 5, 5], "coincide"),
    # b = c: no base
    ([0, 0, 0], [0, 0, 0], [10, 0, 0], [10, 0, 0], "coincide"),
    # a, b, c on one line with dist(a,b) = dist(a,c): passes the length checks
    ([0, 0, 0], [0, 0, 0], [10, 0, 0], [-10, 0, 0], "same line"),
    # not isosceles
    ([0, 0, 0], [0, 0, 0], [10, 0, 0], [0, 12, 0], "not equal"),
    # trapezoid with the small base bigger than the big base
    ([0, 0, 0], [0, 20, 0], [10, 8, 0], [10, 12, 0], "bigger"),
    # trapezoid not flat: c is 8 away from the plane of a1, a2, b
    ([0, 0, 0], [0, 10, 0], [10, 0, 0], [6, 10, 8], "same plane"),
    # trapezoid with a1, a2 and b on one line
    ([0, 0, 0], [0, 4, 0], [0, -10, 0], [0, 14, 0], "same line"),
    # nan and inf
    ([0, 0, np.nan], [0, 0, np.nan], [10, 0, 0], [0, 10, 0], "nan or inf"),
    ([0, 0, 0], [0, 0, 0], [np.inf, 0, 0], [0, 10, 0], "nan or inf"),
])
def test_bad_shapes_are_rejected(a1, a2, b, c, message):
    with pytest.raises(ValueError, match=message):
        extract_slice(VOLUME, a1, a2, b, c)


def test_almost_isosceles_is_accepted():
    # Difference of 0.0005 between the sides, under EPS = 0.001.
    side = 10.0005
    extract_slice(VOLUME, [0, 0, 0], [0, 0, 0], [10, 0, 0], [0, side, 0])


def test_just_not_isosceles_is_rejected():
    # Difference of 0.002, over EPS.
    with pytest.raises(ValueError, match="not equal"):
        extract_slice(VOLUME, [0, 0, 0], [0, 0, 0], [10, 0, 0], [0, 10.002, 0])


def test_negative_coordinates_are_allowed():
    # Points outside the volume are allowed: that part of the image is black.
    image = extract_slice(VOLUME, [-10, 10, 10], [-10, 10, 10], [10, 0, 10], [10, 20, 10])
    assert image.shape[0] > 0
    assert np.any(image == 0)  # outside part
    assert np.any(image == 100)  # inside part


# ---- CSV rows ----

def write_csv(tmp_path, rows):
    path = tmp_path / "planes.csv"
    path.write_text(HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


@pytest.mark.parametrize("row", [
    "3,1,2,3,4,5,6,,,,,,",  # says 3 points but only 2 are given
    "3,1,2,3,4,5,6,7,8,abc,,,",  # text instead of a number
    "5,1,2,3,4,5,6,7,8,9,1,2,3",  # 5 points
    "2,1,2,3,4,5,6,,,,,,",  # 2 points
    "x,1,2,3,4,5,6,7,8,9,,,",  # number of points is not a number
    "4,1,2,3,4,5,6,7,8,9,,,",  # says 4 points but only 3 are given
])
def test_bad_rows_give_the_row_number(tmp_path, row):
    path = write_csv(tmp_path, ["3,0,0,0,10,0,0,0,10,0,,,", row])
    with pytest.raises(ValueError, match="CSV row 3"):
        read_planes(path)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nan_and_inf_are_rejected(tmp_path, value):
    # Python reads "nan" and "inf" as numbers, so they need their own check.
    path = write_csv(tmp_path, [f"3,0,0,{value},10,0,0,0,10,0,,,"])
    with pytest.raises(ValueError, match="CSV row 2"):
        read_planes(path)


def test_empty_csv(tmp_path):
    path = write_csv(tmp_path, [])
    with pytest.raises(ValueError, match="no planes"):
        read_planes(path)


def test_rows_keep_their_order(tmp_path):
    path = write_csv(tmp_path, ["3,0,0,0,10,0,0,0,10,0,,,", "4,0,0,0,10,0,0,0,10,0,10,10,0",
                                "3,1,1,1,11,1,1,1,11,1,,,"])
    planes = read_planes(path)
    assert [row for row, points in planes] == [2, 3, 4]
    assert [len(points) for row, points in planes] == [3, 4, 3]
