import numpy as np

# Smallest length treated as non-zero (also the tolerance used in the assignment).
EPS = 0.001
# Rounding errors: a length of 19.999999999999996 or 20.000000000000004 is 20.
# Used before ceil and floor, so the image size does not depend on the last digit.
TINY = 1e-9


def length(v):
    # Length of a vector, or of each row of an array of vectors.
    # Same formula everywhere, so the fast and the slow versions give the same numbers.
    return np.sqrt(np.sum(v * v, axis=-1))


def check_shape(a1, a2, b, c):
    # Checks that a1, a2, b, c is a valid shape for the algorithm and returns
    # the points as NumPy arrays with the side length dab and the base length dbc.
    # The sides are a1 -> b and a2 -> c, the small base is a1 a2 and the big base is b c.
    # A triangle is a1 = a2 = a.
    # Convert each (x, y, z) point into a NumPy array of decimal numbers.
    # This allows vector operations such as b - a1 and movement between voxels.
    a1 = np.array(a1, dtype=float)
    a2 = np.array(a2, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    if not np.all(np.isfinite([a1, a2, b, c])):
        raise ValueError("A point has a coordinate that is nan or inf.")

    dab = length(b - a1)  # Length of the side a1 -> b.
    dac = length(c - a2)  # Length of the side a2 -> c.
    dbc = length(c - b)  # Distance from b to c (big base).
    d_small = length(a2 - a1)  # Distance from a1 to a2 (0 for a triangle).

    # Degenerate shape: coincident points give an image of height 0
    # (dab) or a zero-length base (dbc) and would cause a division by zero.
    if dab < EPS:
        raise ValueError("Degenerate shape: points a1 and b coincide (dist(a1,b) = 0).")
    if dbc < EPS:
        raise ValueError("Degenerate shape: points b and c coincide (dist(b,c) = 0).")
    # The algorithm requires two sides of the same length: dist(a1,b) = dist(a2,c).
    # v_ac is divided by dab, so a2 only reaches c when both sides are equal.
    if abs(dab - dac) >= EPS:
        raise ValueError(
            f"Sides are not equal: dist(a1,b) = {dab:.4f} but dist(a2,c) = {dac:.4f} "
            f"(difference must be < {EPS})."
        )

    if d_small < EPS:
        check_triangle(a1, b, c, dab)
    else:
        check_trapezoid(a1, a2, b, c, d_small, dbc)

    return a1, a2, b, c, dab, dbc


def check_triangle(a, b, c, dab):
    # a, b, c on one line (for example b and c on both sides of a) pass the
    # checks of check_shape but are not a triangle: c must be away from the line a -> b.
    dist_c_line = length(np.cross(b - a, c - a)) / dab
    if dist_c_line < EPS:
        raise ValueError("Degenerate triangle: a, b and c are on the same line.")


def check_trapezoid(a1, a2, b, c, d_small, dbc):
    # The small base can't be bigger than the big base.
    if d_small > dbc + EPS:
        raise ValueError(
            f"Small base is bigger than big base: dist(a1,a2) = {d_small:.4f} "
            f"but dist(b,c) = {dbc:.4f}."
        )
    # The 4 points must be on the same plane.
    # normal is perpendicular to the plane of a1, a2, b.
    normal = np.cross(a2 - a1, b - a1)
    if length(normal) < EPS:
        raise ValueError("Degenerate trapezoid: a1, a2 and b are on the same line.")
    # distance from c to that plane, must be about 0
    dist_c_plane = abs(np.dot(normal, c - a1)) / length(normal)
    if dist_c_plane >= EPS:
        raise ValueError(
            f"The 4 points are not on the same plane: c is {dist_c_plane:.4f} away from it."
        )


def image_size(dab, dbc):
    # Size of the image E: one row per step along the side, and one more column
    # than the base length, because x1 goes up to floor(d12) included.
    height = int(np.ceil(dab - TINY))
    width = int(np.floor(dbc + TINY)) + 1
    return height, width


def four_points(points):
    # A triangle is a trapezoid where the small base is only one point,
    # so (a, b, c) becomes (a1, a2, b, c) = (a, a, b, c). 4 points stay as they are.
    if len(points) == 3:
        return [points[0], points[0], points[1], points[2]]
    return points


def extract_triangle_slice(volume, a, b, c):
    return extract_slice(volume, *four_points([a, b, c]))


def extract_slice(volume, a1, a2, b, c):
    # Returns the 2D image extracted from the volume, with the professor's algorithm.
    # Same steps as the loop version (tests/slow_slicing.py), but NumPy computes
    # all the rows and all the pixels at once instead of one pixel at a time.
    a1, a2, b, c, dab, dbc = check_shape(a1, a2, b, c)

    v_ab = (b - a1) / dab
    v_ac = (c - a2) / dab

    height, width = image_size(dab, dbc)
    # Same type as the volume, so 16 and 32 bit values are kept as they are.
    E = np.zeros((height, width), dtype=volume.dtype)

    # One step per row, from the start points (no drift).
    # The last step is shorter: height = ceil(dab), so y + 1 can go past b and c,
    # then the row would be wider than the base and x would be out of the image.
    steps = np.minimum(np.arange(1, height + 1), dab)  # y + 1 for row y
    row_a1 = a1 + steps[:, None] * v_ab  # where each row starts, shape (height, 3)
    row_a2 = a2 + steps[:, None] * v_ac  # where each row ends

    d12 = length(row_a2 - row_a1)  # length of each row
    # A row is never wider than the base, but rounding can give 48.00000000000001
    # instead of 48, then x can round up to the width and be out of the image.
    d12 = np.minimum(d12, dbc)
    dp = (row_a2 - row_a1) / d12[:, None]  # step of 1 along each row

    # x1 = 0, 1, 2 ... for every row; row y only uses x1 <= floor(d12[y]).
    x1 = np.arange(width)
    read = x1[None, :] <= np.floor(d12 + TINY)[:, None]  # shape (height, width)

    # Point p = a1 + x1 * dp of every (row, x1), one coordinate at a time.
    # Only the points inside the volume are read, the others stay 0 (black).
    upper = np.array(volume.shape) - 1
    p = []
    for k in range(3):
        pk = row_a1[:, k, None] + x1[None, :] * dp[:, k, None]  # shape (height, width)
        read &= (pk >= 0) & (pk <= upper[k])
        p.append(pk)

    # Round to the nearest voxel; .5 always goes up.
    # p >= 0 here, so cutting the decimals of p + 0.5 is the same as floor(p + 0.5).
    ix = (p[0][read] + 0.5).astype(np.intp)
    iy = (p[1][read] + 0.5).astype(np.intp)
    iz = (p[2][read] + 0.5).astype(np.intp)

    sx, sy, sz = volume.shape
    if volume.flags.f_contiguous:
        # The NRRD volume is stored with x first (index_order="F"): reading with one
        # number per voxel, x + sx * (y + sy * z), is almost 2x faster than volume[ix, iy, iz].
        values = volume.ravel(order="F")[ix + sx * (iy + sy * iz)]
    else:
        values = volume[ix, iy, iz]

    # Column of each point: the row is centered in the image.
    x = (((dbc / 2) - (d12 / 2))[:, None] + x1[None, :]).astype(np.intp)
    y = np.broadcast_to(np.arange(height)[:, None], x.shape)
    E[y[read], x[read]] = values

    return E
