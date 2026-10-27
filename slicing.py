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

    if not (np.all(np.isfinite(a1)) and np.all(np.isfinite(a2))
            and np.all(np.isfinite(b)) and np.all(np.isfinite(c))):
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

    if d_small < EPS:  # triangle
        # a, b, c on one line (for example b and c on both sides of a) pass the
        # checks above but are not a triangle: c must be away from the line a -> b.
        dist_c_line = length(np.cross(b - a1, c - a1)) / dab
        if dist_c_line < EPS:
            raise ValueError("Degenerate triangle: a, b and c are on the same line.")
    else:  # trapezoid
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

    return a1, a2, b, c, dab, dbc


def image_size(dab, dbc):
    # Size of the image E: one row per step along the side, and one more column
    # than the base length, because x1 goes up to floor(d12) included.
    height = int(np.ceil(dab - TINY))
    width = int(np.floor(dbc + TINY)) + 1
    return height, width


def extract_triangle_slice(volume, a, b, c):
    # A triangle is a trapezoid where the small base is only one point,
    # so a1 and a2 both start at a.
    return extract_slice(volume, a, a, b, c)


def extract_slice(volume, a1, a2, b, c):
    # Returns the 2D image extracted from the volume, with the professor's algorithm.
    a1, a2, b, c, dab, dbc = check_shape(a1, a2, b, c)

    v_ab = (b - a1) / dab
    v_ac = (c - a2) / dab

    height, width = image_size(dab, dbc)
    # Same type as the volume, so 16 and 32 bit values are kept as they are.
    E = np.zeros((height, width), dtype=volume.dtype)

    # a1 and a2 start at the given points (both at a for a triangle).
    start1 = a1
    start2 = a2

    for y in range(height):
        # Step from the start points instead of adding v_ab again and again (no drift).
        # The last step is shorter: height = ceil(dab), so y + 1 can go past b and c,
        # then the row would be wider than the base and x would be out of the image.
        step = min(y + 1, dab)
        a1 = start1 + step * v_ab
        a2 = start2 + step * v_ac

        d12 = length(a2 - a1)  # distance between the progressing a1 and a2
        # A row is never wider than the base, but rounding can give 48.00000000000001
        # instead of 48, then x can round up to the width and be out of the image.
        d12 = min(d12, dbc)
        dp = (a2 - a1) / d12  # vector from a1 to a2 normalised

        for x1 in range(int(np.floor(d12 + TINY)) + 1):
            p = a1 + x1 * dp  # from a1 each time (no drift)
            value = 0
            # Use the nearest voxel; volume axes are assumed to be (x, y, z).
            if np.all(p >= 0) and np.all(p <= np.array(volume.shape) - 1):  # inside the volume
                # Round to the nearest voxel; .5 always goes up (p >= 0 here).
                voxel_index = np.floor(p + 0.5).astype(int)
                value = volume[tuple(voxel_index)]

            # Convert the output coordinate to an integer index for NumPy.
            x = int((dbc / 2) - (d12 / 2) + x1)
            E[y, x] = value

    return E
