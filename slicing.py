import numpy as np

# Smallest length treated as non-zero (also the tolerance used in the assignment).
EPS = 0.001


def extract_triangle_slice(volume, a, b, c):
    # A triangle is a trapezoid where the small base is only one point,
    # so a1 and a2 both start at a.
    return extract_slice(volume, a, a, b, c)


def extract_slice(volume, a1, a2, b, c):
    # Returns the 2D image extracted from the volume.
    # The sides are a1 -> b and a2 -> c, the small base is a1 a2 and the big base is b c.
    # Convert each (x, y, z) point into a NumPy array of decimal numbers.
    # This allows vector operations such as b - a1 and movement between voxels.
    a1 = np.array(a1, dtype=float)
    a2 = np.array(a2, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    dab = np.linalg.norm(b - a1)  # Length of the side a1 -> b.
    dac = np.linalg.norm(c - a2)  # Length of the side a2 -> c.
    dbc = np.linalg.norm(c - b)  # Distance from b to c (big base).
    d_small = np.linalg.norm(a2 - a1)  # Distance from a1 to a2 (0 for a triangle).

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

    if d_small >= EPS:  # only for a trapezoid
        # The small base can't be bigger than the big base.
        if d_small > dbc + EPS:
            raise ValueError(
                f"Small base is bigger than big base: dist(a1,a2) = {d_small:.4f} "
                f"but dist(b,c) = {dbc:.4f}."
            )
        # The 4 points must be on the same plane.
        # normal is perpendicular to the plane of a1, a2, b.
        normal = np.cross(a2 - a1, b - a1)
        if np.linalg.norm(normal) < EPS:
            raise ValueError("Degenerate trapezoid: a1, a2 and b are on the same line.")
        # distance from c to that plane, must be about 0
        dist_c_plane = abs(np.dot(normal, c - a1)) / np.linalg.norm(normal)
        if dist_c_plane >= EPS:
            raise ValueError(
                f"The 4 points are not on the same plane: c is {dist_c_plane:.4f} away from it."
            )

    v_ab = (b - a1) / dab
    v_ac = (c - a2) / dab

    height = int(np.ceil(dab))
    # One more column than the base length, x1 goes up to floor(d12) included.
    width = int(np.floor(dbc)) + 1
    E = np.zeros((height, width))

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

        p = a1
        d12 = np.linalg.norm(a2 - a1) #distance between the progressing a1 and a2
        # A row is never wider than the base, but rounding can give 48.00000000000001
        # instead of 48, then x can round up to the width and be out of the image.
        d12 = min(d12, dbc)

        # We can add a check for d12 == 0 before dividing.
        dp = (a2 - a1) / d12 #vector frop a1 to a2 normalised

        # We can add a small tolerance for floating-point rounding errors.
        for x1 in range(int(np.floor(d12)) + 1):
            value = 0
            # Use the nearest voxel; volume axes are assumed to be (x, y, z).
            if np.all(p >= 0) and np.all(p <= np.array(volume.shape) - 1): #if in te interval
                # Round to the nearest voxel; .5 always goes up (p >= 0 here).
                voxel_index = np.floor(p + 0.5).astype(int)
                value = volume[tuple(voxel_index)]

            # Convert the output coordinate to an integer index for NumPy.
            x = int((dbc / 2) - (d12 / 2) + x1)
            # We can check that x is within the output image before writing.
            E[y, x] = value
            p = p + dp

    return E
