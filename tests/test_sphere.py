# Checks that a cut is in the right place, with a gray cube and a white sphere inside.
# A sphere looks the same from every angle, so we can test planes in any direction:
# a plane at distance d from the center cuts the sphere along a disk of radius
# r = sqrt(R^2 - d^2), so the image must have about pi * r^2 white pixels.
#
# Run from the project folder: python -m pytest

import numpy as np
import pytest

from slicing import extract_slice

SIZE = 64  # the volume is SIZE x SIZE x SIZE
CENTER = np.array([32.0, 32.0, 32.0])  # center of the sphere
R = 20  # radius of the sphere
CUBE = 200  # gray value of the cube
SPHERE = 255  # white value of the sphere

# Allowed error, in "ring widths": the disk edge is a staircase because of the
# rounding to the nearest voxel, so we accept half a ring of pixels around the
# edge (2 * pi * r * 0.5). A plane shifted by 1 voxel is already out of this.
TOLERANCE = 0.5


def make_volume():
    # Gray cube with a white sphere in the middle.
    x, y, z = np.meshgrid(np.arange(SIZE), np.arange(SIZE), np.arange(SIZE), indexing="ij")
    volume = np.full((SIZE, SIZE, SIZE), CUBE, dtype=np.uint8)
    inside = (x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2 + (z - CENTER[2]) ** 2 <= R * R
    volume[inside] = SPHERE
    return volume


VOLUME = make_volume()  # made once, used by every test


def random_directions(seed):
    # n = normal of the plane, u and w = two directions inside the plane.
    # n, u and w are perpendicular to each other and have length 1.
    rng = np.random.default_rng(seed)
    n = rng.normal(size=3)
    n = n / np.linalg.norm(n)
    u = np.cross(n, rng.normal(size=3))
    u = u / np.linalg.norm(u)
    w = np.cross(n, u)
    return n, u, w


def square_around(middle, u, w, half_size):
    # Square (trapezoid with equal bases) centered on `middle`, points a1, a2, b, c.
    a1 = middle - half_size * w - half_size * u
    a2 = middle - half_size * w + half_size * u
    b = middle + half_size * w - half_size * u
    c = middle + half_size * w + half_size * u
    return a1, a2, b, c


def count_sphere_pixels(image):
    return int(np.sum(image == SPHERE))


def check_disk(count, radius, stretch=1.0):
    # stretch = how much the algorithm stretches the image vertically (1 for a square).
    expected = np.pi * radius ** 2 * stretch
    allowed = TOLERANCE * 2 * np.pi * radius * stretch
    assert abs(count - expected) <= allowed, f"{count} white pixels, expected about {expected:.0f}"


@pytest.mark.parametrize("seed", range(10))
def test_plane_through_center_gives_disk_of_radius_R(seed):
    n, u, w = random_directions(seed)
    image = extract_slice(VOLUME, *square_around(CENTER, u, w, 24))
    check_disk(count_sphere_pixels(image), R)


@pytest.mark.parametrize("distance", [5, 10, 15, 18])
@pytest.mark.parametrize("seed", range(5))
def test_plane_away_from_center_gives_smaller_disk(distance, seed):
    n, u, w = random_directions(seed)
    image = extract_slice(VOLUME, *square_around(CENTER + distance * n, u, w, 24))
    check_disk(count_sphere_pixels(image), np.sqrt(R ** 2 - distance ** 2))


@pytest.mark.parametrize("seed", range(5))
def test_plane_outside_sphere_has_no_sphere_pixels(seed):
    n, u, w = random_directions(seed)
    image = extract_slice(VOLUME, *square_around(CENTER + 25 * n, u, w, 24))
    assert count_sphere_pixels(image) == 0


@pytest.mark.parametrize("seed", range(5))
def test_same_disk_from_every_angle(seed):
    # Same distance from the center, different angles: about the same number of pixels.
    counts = []
    for angle_seed in range(seed * 10, seed * 10 + 6):
        n, u, w = random_directions(angle_seed)
        image = extract_slice(VOLUME, *square_around(CENTER + 10 * n, u, w, 24))
        counts.append(count_sphere_pixels(image))
    radius = np.sqrt(R ** 2 - 10 ** 2)
    assert max(counts) - min(counts) <= 2 * TOLERANCE * 2 * np.pi * radius


@pytest.mark.parametrize("seed", range(5))
def test_triangle_disk_is_stretched(seed):
    # In the professor's algorithm a row moves by 1 along the side a -> b, not
    # straight down, so a triangle image is stretched vertically by dab / height.
    n, u, w = random_directions(seed)
    height = 90
    half_base = 60
    a = CENTER - height / 2 * w
    b = CENTER + height / 2 * w - half_base * u
    c = CENTER + height / 2 * w + half_base * u
    image = extract_slice(VOLUME, a, a, b, c)
    dab = np.linalg.norm(b - a)
    check_disk(count_sphere_pixels(image), R, stretch=dab / height)


def test_only_known_values():
    # A square bigger than the volume: 0 outside the volume, 200 the cube, 255 the sphere.
    n, u, w = random_directions(0)
    image = extract_slice(VOLUME, *square_around(CENTER, u, w, 60))
    assert set(np.unique(image)) == {0, CUBE, SPHERE}
