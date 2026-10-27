# Software Requirements Specification

## Purpose

The program cuts a 3D volume (an MRI scan, for example) along a plane and saves the cut as an image. Given a list of planes, it saves one image per plane in a video.

It does not display the volume in 3D, edit it, or do any medical analysis.

## Terms

- **Volume (M)**: a 3D grid of integer values. `M[x][y][z]` is one voxel.
- **Plane region**: a triangle or trapezoid, given by 3 or 4 points.
- **Image (E)**: the 2D result of sampling the volume on the plane region.
- **EPS**: tolerance for comparing lengths, `0.001`.

## Input

1. **NRRD file**: a 3D volume of unsigned integers (8, 16 or 32 bits). Each dimension is between 1 and 1023.
2. **CSV file**: one plane per row, with this header:
   `Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4`
   For a triangle the last three columns are empty.
3. **Output path** of the MP4 file.

Run it with: `python Ex0.py file.nrrd file.csv file.mp4`

Coordinates are voxel indices, not millimeters. Points may be outside the volume.

## Functional requirements

| ID | Requirement | Source |
|---|---|---|
| F1 | Read a 3D NRRD volume. | Assignment |
| F2 | Accept a triangle `(a, b, c)` if `abs(dist(a,b) - dist(a,c)) < EPS`. | Assignment |
| F3 | Accept a trapezoid `(a1, a2, b, c)` if `abs(dist(a1,b) - dist(a2,c)) < EPS`, `dist(a1,a2) <= dist(b,c)`, and all four points are on the same plane. | Assignment |
| F4 | Compute the image E with the professor's row-by-row algorithm. | Assignment |
| F5 | Any position outside the volume gives the value 0 (black). | Assignment |
| F6 | Write one video frame per CSV row, in the same order as the CSV. | Assignment |
| F7 | Round a position to the nearest voxel; a value of exactly .5 rounds up. A position is inside the volume if every coordinate is between 0 and size − 1. | My choice |
| F8 | Use the same gray scale for every frame of a video, so the same value always has the same brightness. | My choice |

## Errors

The program stops with a clear message, and does not write a partial video, when:

- the NRRD or CSV file is missing or cannot be read;
- a CSV row is malformed (wrong number of points, a value that is not a number);
- two points of a triangle are the same point (the triangle has no area);
- a triangle or trapezoid breaks the rules in F2 or F3.

The message gives the CSV row number when the problem comes from a row.

## Performance

- At least **30 frames per second** (required), 100 if possible, on a 500×500×500 volume of bytes.
- The speed is measured on computing the slices. Writing the video file is not counted.
- The report states the computer used and the number of frames measured.

## Out of scope

Display of the volume, editing of the volume, medical analysis, other file formats than NRRD.
