# Matala 1: cutting a 3D volume along a plane

Exercise 1 of Introduction to Software Engineering (Ariel University).

The program takes a 3D volume (an MRI scan in NRRD format) and a list of planes, and makes a video with the cut of the volume along each plane: one frame per plane, in the order of the list.

A plane is given by 3 points (an isosceles triangle) or 4 points (an isosceles trapezoid). The cut follows the professor's algorithm: two points go down the two sides of the shape, and each row of the image is read between them.

![Cuts of MRHead turning around the center of the head](docs/images/rotation.png)

## Scope

In scope: reading a NRRD volume, checking the shapes, computing the cuts, writing the MP4 video, measuring the speed.

Out of scope: a graphical interface, 3D display, editing the volume, medical analysis, other file formats.

## Quick start

Python 3.10 or newer.

```powershell
python -m pip install -r requirements.txt
python Ex0.py MRHead_1.nrrd planes_100.csv demo.mp4
```

`MRHead_1.nrrd` is not in the repository (see [docs/DATASET.md](docs/DATASET.md) for the download link).

Other commands:

```powershell
python make_planes.py MRHead_1.nrrd my_planes.csv --mode random --count 100   # make a CSV of planes
python -m pytest                                                              # run the tests
python benchmark.py                                                           # cuts per second on 500^3
```

## CSV format

One plane per row, the same header as the professor's example:

```
Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
3,128,40,40,53,140,40,203,100,120,,,
4,100,60,30,156,60,30,70,180,90,186,180,90
```

Coordinates are voxel indices (not millimeters). With 3 points the order is `a, b, c` with `dist(a,b) = dist(a,c)`. With 4 points it is `a1, a2, b, c`: the small base `a1 a2`, the big base `b c`, and the sides `a1 -> b` and `a2 -> c`.

## Files

| File | What it does |
|---|---|
| `Ex0.py` | the demo: NRRD + CSV -> MP4 |
| `slicing.py` | the checks and the cut (the algorithm) |
| `make_planes.py` | makes CSV files of planes for a volume |
| `benchmark.py` | measures the cuts per second |
| `tests/` | the tests, and `slow_slicing.py`, the first loop version kept as a reference |
| `demo/` | the videos of the experiment |

## Documents

- [SRS.md](SRS.md): what the program must do
- [docs/DESIGN.md](docs/DESIGN.md): the algorithm in detail and the choices we made
- [docs/DATASET.md](docs/DATASET.md): the volumes and the CSV files
- [docs/TESTING.md](docs/TESTING.md): the tests and how to run them
- [docs/EXPERIMENT.md](docs/EXPERIMENT.md): results, speed, videos

## Testing

### How to run

```powershell
python -m pip install -r requirements.txt
python -m pytest                            # all the tests
python -m pytest -q tests/test_sphere.py    # one file
python benchmark.py                         # speed on a 500^3 volume
```

The tests make their own volumes and files (in a temporary folder), so they do not need `MRHead_1.nrrd`.

### Strategy

The hard part is to know the right image. Looking at a cut of the MRI does not prove it is right. So the tests use volumes where we know the answer in advance, and check the result in four ways:

| Level | Idea | File |
|---|---|---|
| Shape | a sphere looks the same from every direction: a plane cuts it along a disk of known size | `test_sphere.py` |
| Position of every pixel | each voxel holds its own coordinates, so each pixel tells which voxel was read; we check it is on the plane, at the right row and the right place in the row | `test_coordinates.py` |
| Exact cuts | small cuts where the whole image can be written by hand | `test_coordinates.py` |
| Same as the reference | the fast NumPy version must give exactly the images of the slow loop version, which follows the pseudo-code line by line | `test_fast_matches_slow.py` |

Then the bad inputs (`test_bad_input.py`) and the demo program itself, with real NRRD, CSV and MP4 files (`test_ex0.py`).

Random planes always come from a fixed seed, so a test gives the same result every time.

### The sphere test

**Why a sphere.** The test volume is a 64×64×64 gray cube (value 200) with a white sphere (value 255) of radius R = 20 in the middle. A sphere looks the same from every direction, so we can cut it with planes in any direction and still know what the image must contain. This is what we need, because the program must work for any plane, not only for X, Y or Z cuts.

**What we expect.** A plane at distance `d` from the center of the sphere cuts it along a disk of radius `r = sqrt(R² − d²)`. If `d > R`, the plane misses the sphere and there is no disk. In the image, one pixel is one step of 1 voxel, so the disk should have about `π · r²` white pixels. We count the white pixels and compare with this number.

Most tests use a square (a trapezoid with equal bases) of side 48, big enough to contain the whole disk. The directions are random but come from fixed seeds.

**Tolerance.** The edge of the disk is a staircase, because each point is rounded to the nearest voxel, so the count is never exactly `π · r²`. We accept an error of half a pixel all around the edge: `allowed error = 0.5 × 2 · π · r`. This is small enough to see a real mistake: if the reading is shifted by one voxel, 34 of the 46 cases fail.

**Triangles are stretched.** In the professor's algorithm, each new row moves by 1 along the side `a → b`, not straight down. When the sides are tilted, the rows are closer than 1 voxel, so the image of a triangle is stretched vertically by `stretch = dab / height of the triangle`. A disk in a triangle image looks a little oval and has `π · r² · stretch` white pixels; the test checks this number. This is how the algorithm works, it is not a bug. A square has no stretch, because its sides are straight down.

**What it does not check.** The sphere test checks the shape of the cut, not the exact place of every pixel: if the direction `a2 → c` is wrong by 3%, all the cases still pass. That is why `test_coordinates.py` uses a volume where each voxel holds its own coordinates, so every pixel can be checked.

**Bug found by this test.** On a square of side 48, a rounding error gave a row length of `48.00000000000001` instead of `48`. The last pixel was then written one column after the end of the image (`IndexError`). Fix in `slicing.py`: a row is never wider than the base, so `d12 = min(d12, dbc)`.

### Do the tests find bugs?

A test that always passes proves nothing. We broke the code on purpose and ran `test_coordinates.py` and `test_sphere.py`:

| Bug put in on purpose | Failed cases |
|---|---|
| `v_ac` 3% too long | 7 |
| rows upside down | 9 |
| columns left-right | 8 |
| round down instead of to the nearest | 9 |
| no step before the first row | 9 |

The sphere test alone did not see the first one: it checks the shape, not the place of each pixel. That is why we have both.

Bugs found by the tests in the real code:

- the last step went past `b` and `c`, and the last row went out of the image (`random_100.csv`);
- `48.00000000000001` instead of `48` gave one column too many (`test_sphere.py`);
- three points on one line with `dist(a,b) = dist(a,c)` were accepted as a triangle (`test_bad_input.py`).

### Test cases

| Test | Input | Expected | Requirement |
|---|---|---|---|
| `test_sphere.py::test_plane_through_center_gives_disk_of_radius_R` | square through the center of the sphere, 10 directions | about π·20² white pixels (± half a pixel around the edge) | FR-4 |
| `test_sphere.py::test_plane_away_from_center_gives_smaller_disk` | square at 5, 10, 15, 18 from the center | about π·(20² − d²) white pixels | FR-4 |
| `test_sphere.py::test_plane_outside_sphere_has_no_sphere_pixels` | square at 25 from the center | no white pixel | FR-4 |
| `test_sphere.py::test_same_disk_from_every_angle` | same distance, 6 directions | about the same count | FR-4 |
| `test_sphere.py::test_triangle_disk_is_stretched` | triangle through the center | π·20² × `dab / height` white pixels | FR-4 |
| `test_sphere.py::test_only_known_values` | square bigger than the volume | only 0, 200 and 255 | FR-4, FR-5 |
| `test_coordinates.py::test_every_pixel_comes_from_the_right_place` | 90 random triangles and trapezoids | each voxel read is at most √3/2 from the plane, at the height of its row, and at the place of its column | FR-4 |
| `test_coordinates.py::test_full_rows_when_the_plane_is_inside_the_volume` | squares of side 20 inside the volume | 20 × 21 image with no black pixel | FR-4 |
| `test_coordinates.py::test_flat_square_is_a_slice_of_the_volume` | square in the layer z = 20 | exactly `M[6:31, 5:31, 20]` | FR-4 |
| `test_coordinates.py::test_layer_number_only` | `M = z + 1`, flat triangle at z = 20 | only 0 and 21 | FR-4 |
| `test_coordinates.py::test_rounding_half_goes_up` | flat square at z = 20.5, 19.5, 20.4, 20.6 | layers 21, 20, 20, 21 | FR-6 |
| `test_coordinates.py::test_first_row_is_one_step_after_a` | square starting at x = 5 | row 0 reads x = 6 | FR-4 |
| `test_coordinates.py::test_last_step_is_shorter` | side of length 10.5 | 11 rows, the last one reads x = 16 | FR-4 |
| `test_coordinates.py::test_outside_volume_is_black` | square with y from −10 to 10 | columns 0–9 black, 10–20 read | FR-5 |
| `test_coordinates.py::test_plane_completely_outside_is_all_black` | square far away | all black | FR-5 |
| `test_coordinates.py::test_values_keep_their_type` | 8, 16, 32-bit volume with the maximum value | same type, same maximum | FR-7 |
| `test_fast_matches_slow.py` (3 tests) | 110 random and 36 turning planes, 2 memory orders | exactly the same images | FR-4, NFR-1 |
| `test_bad_input.py::test_bad_shapes_are_rejected` | 9 bad shapes: coincident points, `b = c`, flat triangle, unequal sides, small base too big, bent trapezoid, nan, inf | error with the reason | FR-2, FR-3, ER-3 |
| `test_bad_input.py::test_almost_isosceles_is_accepted` | sides differ by 0.0005 | accepted | FR-2 |
| `test_bad_input.py::test_just_not_isosceles_is_rejected` | sides differ by 0.002 | rejected | FR-2 |
| `test_bad_input.py::test_negative_coordinates_are_allowed` | triangle half at x < 0 | no error, black part and read part | FR-5 |
| `test_bad_input.py::test_bad_rows_give_the_row_number` | 6 bad rows (2 points, text, 5 points, ...) | error with "CSV row 3" | ER-2 |
| `test_bad_input.py::test_nan_and_inf_are_rejected` | `nan`, `inf`, `-inf` | error with the row number | ER-2 |
| `test_bad_input.py::test_empty_csv` | header only | error "no planes" | ER-2 |
| `test_bad_input.py::test_rows_keep_their_order` | 3 rows | rows 2, 3, 4 in this order | FR-8 |
| `test_ex0.py::test_nrrd_types_are_read_with_x_first` | real NRRD files of 8, 16, 32 bits | right shape, type and value | FR-1 |
| `test_ex0.py::test_missing_file_gives_an_error` | NRRD file missing | error | ER-1 |
| `test_ex0.py::test_one_frame_per_row` | CSV of 3 rows | MP4 with 3 frames | FR-8 |
| `test_ex0.py::test_bad_row_leaves_no_video` | row 3 not isosceles | error "CSV row 3", no MP4 file | ER-3, ER-4 |
| `test_ex0.py::test_bad_row_keeps_an_old_video` | bad row, old `out.mp4` | old file not changed | ER-4 |

### Not tested automatically

- The gray scale and the frame size of the video (FR-9, FR-10): checked by watching the videos in `demo/`.
- The speed (NFR-1): measured with `benchmark.py` and `Ex0.py`, see [docs/EXPERIMENT.md](docs/EXPERIMENT.md). A speed test in pytest would depend on the computer.

## Use of AI

I used Claude Code as a coding assistant. The ideas are mine: the approach,
the checks on the shapes, the choices in DESIGN.md (rounding, borders,
gray scale, frame size) and the test ideas (sphere, voxels that hold their
own coordinates, comparison with the slow version). The AI turned my
pseudo-code into Python and helped with the NumPy version. I read, ran and
checked all the code with the tests.
