# Software Requirements Specification

## 1. Introduction

The program cuts a 3D volume (an MRI scan, for example) along a plane and saves the cut as an image. Given a list of planes, it saves one image per plane in a video.

It does not display the volume in 3D, edit it, or do any medical analysis.

References: the exercise text (Ex1, Intro2SE), the lectures of 21 and 25 October 2026.

### Terms

- **Volume (M)**: a 3D grid of integer values. `M[x][y][z]` is one voxel.
- **Shape**: a triangle or trapezoid, given by 3 or 4 points, that defines the plane and the part of it to cut.
- **Image (E)**: the 2D result of the cut.
- **EPS**: tolerance for comparing lengths, `0.001`.

## 2. Overall description

**Users**: a student or the professor, who runs the program from the command line and watches the video in a player like VLC.

**Environment**: Python 3.10 or newer on Windows, Linux or macOS, with the packages of `requirements.txt`.

**Inputs**

1. **NRRD file**: a 3D volume of unsigned integers (8, 16 or 32 bits). Each dimension is between 1 and 1023.
2. **CSV file**: one plane per row, with this header:
   `Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4`
   For a triangle the last three cells are empty.
3. **Output path** of the MP4 file.

Coordinates are voxel indices, not millimeters. Points may be outside the volume.

### Use case UC-01: make a video from a list of planes

Actor: the user.

1. The user runs `python Ex0.py file.nrrd file.csv file.mp4`.
2. The system reads the volume and the CSV, and checks every shape.
3. The system computes the cut of each shape, in the CSV order.
4. The system writes the video, one frame per row, and prints the number of frames and the speed of the cuts.

Alternative 2a: a file is missing or a row is wrong. The system prints the error with the row number and stops. No video is written, and an old file with the same name is kept.

## 3. Requirements

### Functional

| ID | Requirement | Source |
|---|---|---|
| FR-1 | The system shall read a 3D NRRD volume of unsigned 8, 16 or 32-bit integers, with x as the first index. | Assignment |
| FR-2 | The system shall accept a triangle `(a, b, c)` only if `abs(dist(a,b) - dist(a,c)) < EPS` and the 3 points are not on one line. | Assignment, line check is my choice |
| FR-3 | The system shall accept a trapezoid `(a1, a2, b, c)` only if `abs(dist(a1,b) - dist(a2,c)) < EPS`, `dist(a1,a2) <= dist(b,c)`, and the 4 points are on one plane (within EPS). | Assignment |
| FR-4 | The system shall compute the image E with the professor's row-by-row algorithm. | Assignment |
| FR-5 | A position outside the volume shall give the value 0 (black). A position is inside if every coordinate is between 0 and size − 1. | Assignment, border is my choice |
| FR-6 | A position shall be rounded to the nearest voxel; exactly .5 rounds up. | My choice |
| FR-7 | The image shall keep the values and the type of the volume. | My choice |
| FR-8 | The system shall write one video frame per CSV row, in the same order. | Assignment |
| FR-9 | All the frames of a video shall use the same gray scale (0 black, maximum of the volume white). | My choice |
| FR-10 | Each frame shall have the same size; a smaller image is centered on a black background. | My choice (a video needs one size) |

### Errors

| ID | Requirement |
|---|---|
| ER-1 | A missing or unreadable file shall stop the program with a clear message. |
| ER-2 | A wrong CSV row (wrong number of points, empty cell, text, nan, inf) shall stop the program with the row number. |
| ER-3 | A shape that breaks FR-2 or FR-3 (coincident points, unequal sides, flat or bent shape) shall stop the program with the row number. |
| ER-4 | After an error, no video shall be written, and an existing file with the same name shall not change. |

### Non-functional

| ID | Requirement |
|---|---|
| NFR-1 | The system shall compute at least 30 cuts per second (required), 100 if possible, on a 500×500×500 volume of bytes. Only the cuts are measured, not the file reading or the video writing. |
| NFR-2 | The speed report shall give the computer, the number of cuts and the kind of planes. |
| NFR-3 | The code shall keep the checks, the cut, the CSV reading and the video writing in separate functions. |
| NFR-4 | Installation shall need only `pip install -r requirements.txt`. |

## 4. Traceability

| Requirement | Tests (folder `tests/`) |
|---|---|
| FR-1 | `test_ex0.py::test_nrrd_types_are_read_with_x_first` |
| FR-2, FR-3, ER-3 | `test_bad_input.py::test_bad_shapes_are_rejected`, `test_almost_isosceles_is_accepted`, `test_just_not_isosceles_is_rejected` |
| FR-4 | `test_coordinates.py` (all), `test_sphere.py` (all), `test_fast_matches_slow.py` |
| FR-5 | `test_coordinates.py::test_outside_volume_is_black`, `test_plane_completely_outside_is_all_black`, `test_bad_input.py::test_negative_coordinates_are_allowed` |
| FR-6 | `test_coordinates.py::test_rounding_half_goes_up` |
| FR-7 | `test_coordinates.py::test_values_keep_their_type` |
| FR-8 | `test_ex0.py::test_one_frame_per_row`, `test_bad_input.py::test_rows_keep_their_order` |
| FR-9, FR-10 | `test_ex0.py::test_same_value_same_gray_in_every_frame`, `test_small_image_is_in_the_middle_of_a_black_frame`, and by watching the videos |
| ER-1 | `test_ex0.py::test_missing_file_gives_an_error` |
| ER-2 | `test_bad_input.py::test_bad_rows_give_the_row_number`, `test_nan_and_inf_are_rejected`, `test_empty_csv` |
| ER-4 | `test_ex0.py::test_bad_row_leaves_no_video`, `test_bad_row_keeps_an_old_video` |
| NFR-1, NFR-2 | `benchmark.py`, results in [docs/EXPERIMENT.md](docs/EXPERIMENT.md) |
