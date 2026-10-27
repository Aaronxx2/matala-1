# The fast version (slicing.py, NumPy on whole arrays) must give exactly the same
# images as the slow version (tests/slow_slicing.py, one pixel at a time),
# which follows the professor's pseudo-code line by line.

import numpy as np
import pytest

from make_planes import random_planes, rotating_planes
from slicing import extract_slice
from slow_slicing import slow_extract_slice


def four_points(points):
    if len(points) == 3:
        return [points[0], points[0], points[1], points[2]]
    return points


def coordinate_volume(shape):
    # Every voxel has a different value, so any difference shows.
    values = np.arange(1, np.prod(shape) + 1, dtype=np.uint32)
    return values.reshape(shape, order="F")


@pytest.mark.parametrize("seed", range(4))
def test_random_planes(seed):
    volume = coordinate_volume((40, 50, 30))
    for points in random_planes(volume.shape, 25, seed):
        fast = extract_slice(volume, *four_points(points))
        slow = slow_extract_slice(volume, *four_points(points))
        assert np.array_equal(fast, slow)


@pytest.mark.parametrize("axis", [0, 1, 2])
def test_rotating_planes(axis):
    volume = coordinate_volume((40, 50, 30))
    for points in rotating_planes(volume.shape, 12, axis):
        assert np.array_equal(extract_slice(volume, *points), slow_extract_slice(volume, *points))


def test_volume_not_stored_with_x_first():
    # slicing.py reads faster when x is first in memory (NRRD order); check the other case too.
    volume = np.ascontiguousarray(coordinate_volume((40, 50, 30)))
    for points in random_planes(volume.shape, 10, 7):
        fast = extract_slice(volume, *four_points(points))
        slow = slow_extract_slice(volume, *four_points(points))
        assert np.array_equal(fast, slow)
