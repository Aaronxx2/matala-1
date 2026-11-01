# Sphere test

File: `tests/test_sphere.py`. Run it from the project folder with `python -m pytest`.

## Why a sphere

To check that a cut is in the right place, we need a volume where we know the answer in advance.

The test volume is a 64×64×64 gray cube (value 200) with a white sphere (value 255) of radius R = 20 in the middle.

A sphere looks the same from every direction. So we can cut it with planes in any direction, and still know what the image must contain. This is what we need, because the program must work for any plane, not only for X, Y or Z cuts.

## What we expect

A plane at distance `d` from the center of the sphere cuts it along a disk of radius:

```
r = sqrt(R² − d²)
```

If `d > R`, the plane misses the sphere and there is no disk.

In the image, one pixel is one step of 1 voxel, so the disk should have about `π · r²` white pixels.

We count the white pixels and compare with this number.

## The tests

| Test | Plane | Expected |
|---|---|---|
| `test_plane_through_center_gives_disk_of_radius_R` | through the center, 10 random directions | about π · 20² white pixels |
| `test_plane_away_from_center_gives_smaller_disk` | at 5, 10, 15 and 18 voxels from the center | a smaller disk, of radius sqrt(R² − d²) |
| `test_plane_outside_sphere_has_no_sphere_pixels` | at 25 voxels from the center | no white pixel |
| `test_same_disk_from_every_angle` | same distance, 6 directions | about the same number of white pixels |
| `test_triangle_disk_is_stretched` | a triangle through the center | a disk stretched by `dab / height` (see below) |
| `test_only_known_values` | a square bigger than the volume | only 0 (outside), 200 (cube) and 255 (sphere) |

Most tests use a square (a trapezoid with equal bases) of side 48, big enough to contain the whole disk. The directions are random but come from fixed seeds, so the test gives the same result every time.

## Tolerance

The edge of the disk is a staircase, because each point is rounded to the nearest voxel. So the count is never exactly `π · r²`.

We accept an error of half a pixel all around the edge of the disk:

```
allowed error = 0.5 × 2 · π · r
```

This is small enough to see a real mistake: if the reading is shifted by one voxel, 34 of the 46 cases fail.

## Triangles are stretched

In the professor's algorithm, each new row moves by 1 along the side `a → b`, not straight down. When the sides are tilted, the rows are closer than 1 voxel, so the image of a triangle is stretched vertically by:

```
stretch = dab / height of the triangle
```

A disk in a triangle image looks a little oval, and has `π · r² · stretch` white pixels. The test checks this number. This is how the algorithm works, it is not a bug. A square has no stretch, because its sides are straight down.

## What this test does not check

The sphere test checks the shape of the cut, not the exact place of every pixel. For example, if the direction `a2 → c` is wrong by 3%, all the cases still pass.

That is why `test_coordinates.py` uses a volume where each voxel holds its own coordinates, so every pixel can be checked.

## Bug found by this test

On a square of side 48, a rounding error gave a row length of `48.00000000000001` instead of `48`. The last pixel was then written one column after the end of the image (`IndexError`).

Fix in `slicing.py`: a row is never wider than the base, so `d12 = min(d12, dbc)`.
