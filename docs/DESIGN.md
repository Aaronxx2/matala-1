# Design of the algorithm

This document explains how a cut is computed, and every choice we had to make because the pseudo-code does not say it. The code is in `slicing.py`.

## 1. From the files to the video

```
Ex0.py
  load_volume()   NRRD file -> 3D array M[x][y][z]
  read_planes()   CSV file  -> list of (row number, 3 or 4 points)
  check_shape()   for every row, before writing anything      (slicing.py)
  extract_slice() for every row: the image E                  (slicing.py)
  frame           E -> gray levels 0..255, centered in a fixed size frame
  imageio         frames -> MP4 (temporary file, renamed at the end)
```

## 2. Coordinates

The points are **voxel indices**: `(10, 20, 30)` is the voxel `M[10][20][30]`. They are not millimeters.

The NRRD file is read with x as the first index (`index_order="F"`), like in the file.

In MRHead a voxel is 1 × 1 × 1.3 mm. The algorithm works on indices, so a cut along the third axis looks a little squashed compared to the real head. We keep it this way: the exercise defines the volume as a matrix of indices.

## 3. The shape

```
            a1 ------- a2           small base (one point for a triangle: a1 = a2 = a)
           /             \
          /   row y       \         row y goes from the point on a1 -> b
         /  ............   \        to the point on a2 -> c
        /                   \
       b ------------------- c      big base
```

- A triangle `(a, b, c)` is handled as the trapezoid `(a, a, b, c)`. One code for both.
- In the CSV a trapezoid is written side by side, `a1, b, a2, c`, like the professor's example (with the order `a1, a2, b, c` its row 5 would have sides of 300 and 400 instead of 502.5 and 502.5). `four_points` in `slicing.py` puts the points in the order `a1, a2, b, c` used by the cut.
- The sides `a1 -> b` and `a2 -> c` have the same length `dab`. The big base `b c` has length `dbc`.

## 4. The cut, step by step

This is the professor's algorithm. The words in *italics* are our additions, explained in section 5.

1. `dab = dist(a1, b)`, `dbc = dist(b, c)`.
2. `v_ab = (b - a1) / dab`, `v_ac = (c - a2) / dab`: one step of length 1 along each side.
3. The image E has `ceil(dab)` rows and `floor(dbc) + 1` columns, filled with 0.
4. For each row `y = 0, 1, ...`:
   1. *`step = min(y + 1, dab)`*, then `a1' = a1 + step * v_ab` and `a2' = a2 + step * v_ac`.
   2. `d12 = dist(a1', a2')`, *at most `dbc`*. `dp = (a2' - a1') / d12`.
   3. For `x1 = 0, 1, ..., floor(d12)`:
      - `p = a1' + x1 * dp`
      - if `p` is inside the volume, `v` = the voxel nearest to `p`, otherwise `v = 0`
      - `x = int(dbc / 2 - d12 / 2 + x1)`: the row is centered
      - `E[y][x] = v`

## 5. Choices the pseudo-code leaves open

| Question | Our choice | Why |
|---|---|---|
| Read a point between voxels | nearest voxel, `floor(p + 0.5)`: .5 always goes up | simple and fast; `round()` in NumPy sends .5 to the even number, which is harder to explain |
| Inside the volume | every coordinate between 0 and size − 1 | these are the centers of the first and last voxels |
| First row | one step after `a1` (the pseudo-code moves before reading) | we keep the pseudo-code; so `a` itself is never read |
| Last row | `ceil(dab)` steps would go past `b` and `c` by less than 1: the last step is shortened to stop at `b` and `c` | otherwise the last row is wider than the base and goes out of the image |
| Image size | `ceil(dab)` rows, `floor(dbc) + 1` columns | `x1` goes up to `floor(d12)` included, so a full row needs one more column than `dbc` |
| Rounding errors | before `ceil` and `floor`, a length within `1e-9` of an integer is that integer; `d12` is never bigger than `dbc` | a square of side 48 gave `48.00000000000001` and an extra column out of the image (found by the sphere test) |
| Position of a point | always from the start point: `a1 + step * v_ab`, `a1' + x1 * dp` | adding `v_ab` many times adds up rounding errors |
| Value type | E has the type of the volume | 16 and 32-bit values are not changed |

### Checks before the cut

The cut is computed only for a valid shape. Otherwise the program stops with the reason (and the CSV row number in `Ex0.py`).

| Check | Why |
|---|---|
| no `nan` or `inf` | Python reads `"nan"` as a number |
| `dab >= EPS` and `dbc >= EPS` | a length of 0 means no row or no base, and a division by 0 |
| `abs(dist(a1,b) - dist(a2,c)) < EPS` | `v_ac` is divided by `dab`: with unequal sides, `a2` does not reach `c` |
| triangle: `c` not on the line `a -> b` | `a=(0,0,0), b=(10,0,0), c=(-10,0,0)` has equal sides but is flat |
| trapezoid: `dist(a1,a2) <= dist(b,c)` | asked by the exercise |
| trapezoid: `a1, a2, b` not on one line, and `c` on their plane (within EPS) | otherwise there is no plane |

`EPS = 0.001` comes from the exercise.

### A property to know: triangles are stretched

Each row moves by 1 **along the side**, not straight down. When the sides are tilted, two rows are closer than 1 voxel. So the image of a triangle is stretched vertically by `dab / height`, where `height` is the distance from `a` to the base. A circle in the volume looks like an ellipse in the image. A rectangle (sides perpendicular to the bases) is not stretched. This is how the algorithm works; we do not change it.

## 6. The fast version

The first version (now `tests/slow_slicing.py`) does one pixel at a time in Python. It gave about 1 cut per second on MRHead, far from the 30 required.

`slicing.py` does exactly the same steps, but on whole arrays with NumPy:

1. All the rows at once: `step` is an array of `height` numbers, so `a1'`, `a2'`, `d12` and `dp` are arrays of rows.
2. All the pixels at once: `p = a1' + x1 * dp` for every row and every `x1`, one coordinate (x, y, z) at a time. Each is a `height × width` array.
3. A boolean array `read` keeps the pixels that are in their row (`x1 <= floor(d12)`) and inside the volume.
4. The voxels are read all together. When the volume has x first in memory (NRRD), each voxel is found with one number, `x + sx * (y + sy * z)`, which is almost 2 times faster than `M[x, y, z]` with three arrays (measured: 3.9 ms instead of 6.8 ms for the biggest cut).

The formulas are the same, in the same order, so the two versions give exactly the same images: `tests/test_fast_matches_slow.py` checks it on many planes.

Memory: three `height × width` arrays of float64. For the biggest cut of a 500³ volume (a square through the whole volume, about 500 × 710 pixels) this is about 8.5 MB.

## 7. The video

- **Gray scale**: one scale for the whole video, from 0 (black) to the maximum of the volume (white). The same value has the same gray in every frame. The cost: MRHead has a few very bright voxels (max 279, while 99.9% of the voxels are 152 or less), so the video is rather dark.
- **Frame size**: a video has one size. Each image is centered on a black frame as big as the biggest image of the CSV, rounded up to a multiple of 16 (video encoders work on blocks of 16 pixels).
- **Errors**: all the shapes are checked before the first frame. The video is written to `name.tmp.mp4` and renamed at the end, so an error never leaves a broken video and never replaces an old one.
- `--fps` is the playback speed of the video only. It has nothing to do with the speed of the cuts.

## 8. Ideas we did not keep

| Idea | Why not |
|---|---|
| Plane equation `ax + by + cz + d = 0`, keep the voxels where `z` is an integer (my first idea) | gives a list of points, not an image; misses most of the plane when it is tilted; fails when `c = 0` |
| Trilinear interpolation (mix of the 8 voxels around `p`) | smoother image but 8 reads per pixel, and not needed by the exercise |
| float32 instead of float64 | a little faster, but the rounding would no longer be exactly the same as the reference version |
