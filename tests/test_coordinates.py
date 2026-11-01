# Checks where every pixel comes from.
# Each voxel holds its own position: M[x][y][z] = 1 + x + N*y + N*N*z, so the value of
# a pixel tells exactly which voxel was read (0 is kept for "outside the volume").
#
# Two kinds of tests:
# - properties on many random planes: the voxel read is on the plane, at the right
#   height and the right place along the row (this catches flipped or mixed pixels);
# - simple cuts where the whole image can be written by hand.
#
# Run from the project folder: python -m pytest

import numpy as np
import pytest

from make_planes import random_planes, rotating_planes
from slicing import extract_slice, four_points

N = 40  # the volume is N x N x N
MARGIN = np.sqrt(3) / 2  # max distance between a point and the center of its rounded voxel


def coordinate_volume(n=N):
    # M[x][y][z] = 1 + x + n*y + n*n*z, stored with x first like a NRRD volume.
    # The biggest value is n**3, it needs 32 bits (n = 40 gives 64000).
    values = np.arange(1, n ** 3 + 1, dtype=np.uint32)
    return values.reshape((n, n, n), order="F")


def decode(image, n=N):
    # Gives back x, y, z of the voxel read for each pixel (only for pixels > 0).
    v = image.astype(np.int64) - 1
    return v % n, (v // n) % n, v // (n * n)


VOLUME = coordinate_volume()


@pytest.mark.parametrize("seed", range(6))
def test_every_pixel_comes_from_the_right_place(seed):
    # Random triangles and trapezoids around the volume (some points outside).
    for points in random_planes(VOLUME.shape, 15, seed):
        a1, a2, b, c = [np.array(p, dtype=float) for p in four_points(points)]
        image = extract_slice(VOLUME, a1, a2, b, c)

        dab = np.linalg.norm(b - a1)
        dbc = np.linalg.norm(c - b)
        small_mid = (a1 + a2) / 2  # middle of the small base
        big_mid = (b + c) / 2  # middle of the big base
        height = np.linalg.norm(big_mid - small_mid)  # distance between the bases
        down = (big_mid - small_mid) / height  # from the small base to the big base
        across = (c - b) / dbc  # along the bases, from the a1 side to the a2 side
        normal = np.cross(down, across)  # perpendicular to the plane

        rows, cols = np.nonzero(image)
        x, y, z = decode(image[rows, cols])
        q = np.stack([x, y, z], axis=1) - small_mid  # voxel read, from the small base middle

        # 1. On the plane.
        assert np.all(np.abs(q @ normal) <= MARGIN + 1e-9)

        # 2. Right height: row y is min(y + 1, dab) steps along the side, which is
        #    min(y + 1, dab) * height / dab away from the small base.
        expected_down = np.minimum(rows + 1, dab) * height / dab
        assert np.all(np.abs(q @ down - expected_down) <= MARGIN + 1e-9)

        # 3. Right place along the row: column x covers [x, x + 1) minus half the base,
        #    measured from the middle line of the shape.
        along = q @ across
        assert np.all(along >= cols - dbc / 2 - MARGIN - 1e-9)
        assert np.all(along <= cols + 1 - dbc / 2 + MARGIN + 1e-9)


@pytest.mark.parametrize("seed", range(3))
def test_full_rows_when_the_plane_is_inside_the_volume(seed):
    # Squares turning around the center, small enough to stay inside the volume:
    # row y must have exactly floor(d12) + 1 pixels, no black pixel inside the shape.
    center = np.array([(N - 1) / 2] * 3)
    rng = np.random.default_rng(seed)
    for _ in range(5):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        w = np.cross(u, rng.normal(size=3))
        w = w / np.linalg.norm(w)
        a1, a2 = center - 10 * w - 10 * u, center - 10 * w + 10 * u
        b, c = center + 10 * w - 10 * u, center + 10 * w + 10 * u
        image = extract_slice(VOLUME, a1, a2, b, c)
        # Square of side 20: 20 rows of 21 pixels (floor(20) + 1).
        assert image.shape == (20, 21)
        assert np.all(image > 0)


def test_flat_square_is_a_slice_of_the_volume():
    # Square in the layer z = 20, sides along x, bases along y.
    # Row y is one step after a1, so it reads x = 6 + y; column x reads y = 5 + x.
    image = extract_slice(VOLUME, [5, 5, 20], [5, 30, 20], [30, 5, 20], [30, 30, 20])
    assert image.shape == (25, 26)
    assert np.array_equal(image, VOLUME[6:31, 5:31, 20])


def test_layer_number_only():
    # The simple version of the idea: M[x][y][z] = z + 1.
    # A flat triangle in the layer z = 20 must read 21 in every pixel of the shape.
    volume = np.zeros((N, N, N), dtype=np.uint8)
    volume[:, :, :] = np.arange(1, N + 1, dtype=np.uint8)[None, None, :]
    image = extract_slice(volume, [5, 20, 20], [5, 20, 20], [30, 5, 20], [30, 35, 20])
    assert set(np.unique(image)) == {0, 21}  # 0 outside the triangle, 21 inside


@pytest.mark.parametrize("z, expected_layer", [(20.5, 21), (19.5, 20), (20.4, 20), (20.6, 21)])
def test_rounding_half_goes_up(z, expected_layer):
    image = extract_slice(VOLUME, [5, 5, z], [5, 30, z], [30, 5, z], [30, 30, z])
    x, y, layer = decode(image)
    assert np.all(layer == expected_layer)


def test_first_row_is_one_step_after_a():
    # The pseudo-code moves a1 before reading, so the point a itself is never read.
    image = extract_slice(VOLUME, [5, 5, 20], [5, 30, 20], [30, 5, 20], [30, 30, 20])
    x, y, z = decode(image[0])
    assert np.all(x == 6)


def test_last_step_is_shorter():
    # dab = 10.5: 11 rows, the last row is at b (x = 15.5, rounded up to 16), not after it.
    image = extract_slice(VOLUME, [5, 5, 20], [5, 25, 20], [15.5, 5, 20], [15.5, 25, 20])
    assert image.shape[0] == 11
    x, y, z = decode(image)
    assert x[:-1].max() == 15  # rows 0 to 9 read x = 6 to 15
    assert np.all(decode(image[-1])[0] == 16)  # row 10 reads x = 15.5 -> 16


def test_outside_volume_is_black():
    # Bases along y from -10 to 10: the points with y < 0 are outside the volume.
    # Column x reads y = -10 + x, so columns 0 to 9 are black and 10 to 20 are read.
    image = extract_slice(VOLUME, [5, -10, 20], [5, 10, 20], [25, -10, 20], [25, 10, 20])
    assert np.all(image[:, :10] == 0)
    assert np.all(image[:, 10:] > 0)


def test_plane_completely_outside_is_all_black():
    image = extract_slice(VOLUME, [100, 5, 5], [100, 30, 5], [130, 5, 5], [130, 30, 5])
    assert np.all(image == 0)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
def test_values_keep_their_type(dtype):
    # The image has the same type as the volume, and the biggest value is not changed.
    volume = np.zeros((10, 10, 10), dtype=dtype)
    volume[7, 5, 5] = np.iinfo(dtype).max  # row 0 reads x = 6, row 1 reads x = 7
    image = extract_slice(volume, [5, 0, 5], [5, 9, 5], [9, 0, 5], [9, 9, 5])
    assert image.dtype == dtype
    assert image.max() == np.iinfo(dtype).max


def test_rotating_planes_stay_on_their_plane():
    # Same check as above with the planes of the demo video.
    for points in rotating_planes(VOLUME.shape, 12, 1):
        a1, a2, b, c = [np.array(p) for p in points]
        image = extract_slice(VOLUME, a1, a2, b, c)
        normal = np.cross(a2 - a1, b - a1)
        normal = normal / np.linalg.norm(normal)
        x, y, z = decode(image[image > 0])
        q = np.stack([x, y, z], axis=1) - a1
        assert np.all(np.abs(q @ normal) <= MARGIN + 1e-9)


def test_triangle_is_the_trapezoid_with_a1_equal_a2():
    # A triangle (a, b, c) is cut like the trapezoid (a, a, b, c); 4 points stay as they are.
    a, b, c = [5, 20, 20], [30, 5, 20], [30, 35, 20]
    assert four_points([a, b, c]) == [a, a, b, c]
    assert four_points([a, a, b, c]) == [a, a, b, c]
