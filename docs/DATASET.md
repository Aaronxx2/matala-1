# Data

## Volumes

### MRHead (the professor's file)

| | |
|---|---|
| File | `MRHead_1.nrrd`, 6.9 MB, from the 3D Slicer sample data |
| Download | [link given in the exercise](https://drive.google.com/file/d/1cqqOgSf8k4e14K5CBs-V_EvMmATX1K-J/view?usp=sharing), put it in the project folder |
| Size | 256 × 256 × 130 voxels |
| Type | `short`: signed 16-bit integers, values 0 to 279 |
| Voxel size | 1 × 1 × 1.3 mm |
| Axes | index 0 goes to the back of the head, index 1 goes down (index 0 is the top of the head), index 2 goes from left to right |

It is not in the repository (`.gitignore` has `*.nrrd`): it is big and it is not ours.

The exercise asks for unsigned integers. MRHead is signed, but all its values are positive, and the program reads it like any other integer type.

### Test volumes

The tests build their own small volumes, in memory or as real NRRD files in a temporary folder. We know exactly what is inside, so we know the right answer.

| Volume | Where | What it checks |
|---|---|---|
| Gray cube (200) with a white sphere (255) of radius 20, 64³ | `tests/test_sphere.py` | the shape of the cut, in any direction |
| `M[x][y][z] = 1 + x + 40*y + 1600*z`, 40³, 32 bits | `tests/test_coordinates.py` | each pixel tells which voxel was read |
| `M[x][y][z] = z + 1`, 40³ | `tests/test_coordinates.py` | the simple version: a flat cut reads one layer |
| one voxel at the maximum of 8, 16 and 32 bits | `tests/test_coordinates.py`, `tests/test_ex0.py` | values and types are kept, NRRD files of each type are read with x first |
| random bytes, 500³ | `benchmark.py` | speed |

## Plane files (CSV)

| File | Content |
|---|---|
| `points.csv` | 2 planes by hand: a triangle and a trapezoid inside MRHead |
| `planes_100.csv` | 100 squares turning around the center of MRHead (`make_planes.py --mode rotate`) |
| `random_100.csv` | 100 random triangles and trapezoids in all directions, most with points outside the volume (`make_planes.py --mode random --seed 0`) |
| `professor_example.csv` | the example from the exercise |

`make_planes.py` reads only the header of a NRRD file, so it makes planes for any volume size.

### The professor's example

It shows the format, and its points are made for a bigger volume (about 500³), so on MRHead most of each cut is black.

Its trapezoids tell the order of the 4 points: read side by side, `a1, b, a2, c`, row 5 has two sides of 502.5 (an isosceles trapezoid with bases of 300 and 400). Read as `a1, a2, b, c`, the same row would have sides of 300 and 400. So the program uses `a1, b, a2, c`.

Row 4 breaks the exercise's own rules: it is a triangle with `dist(a,b) = 497.39` but `dist(a,c) = 476.86`. So `Ex0.py` stops at row 4. This is a question for the professor.
