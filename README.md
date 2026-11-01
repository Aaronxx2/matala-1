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
4,100,60,30,70,180,90,156,60,30,186,180,90
```

Coordinates are voxel indices (not millimeters). With 3 points the order is `a, b, c` with `dist(a,b) = dist(a,c)`. With 4 points it is `a1, b, a2, c`, one side after the other: the side `a1 -> b`, then the side `a2 -> c`, with `dist(a1,b) = dist(a2,c)`. The small base is `a1 a2` and the big base is `b c`. This is the order of the professor's example: with it, its trapezoids are isosceles.

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

`python -m pytest` runs the 113 tests in a few seconds. They build their own volumes, so they do not need `MRHead_1.nrrd`.

The tests use volumes where the right answer is known in advance:

- **a sphere**: a plane cuts it along a disk of known size, in any direction (`test_sphere.py`);
- **voxels that hold their own coordinates**: each pixel tells which voxel was read (`test_coordinates.py`);
- **the slow version**: the fast NumPy version must give exactly the same images as the loop version that follows the pseudo-code (`test_fast_matches_slow.py`);
- **bad inputs and the demo itself**, with real NRRD, CSV and MP4 files (`test_bad_input.py`, `test_ex0.py`).

All the test cases, and the bugs put in on purpose to check that the tests find them: [docs/TESTING.md](docs/TESTING.md).

## Use of AI

I used Claude Code as a coding assistant. The ideas are mine: the approach,
the checks on the shapes, the choices in DESIGN.md (rounding, borders,
gray scale, frame size) and the test ideas (sphere, voxels that hold their
own coordinates, comparison with the slow version). The AI turned my
pseudo-code into Python and helped with the NumPy version. I read, ran and
checked all the code with the tests.
