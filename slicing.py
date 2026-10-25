import numpy as np


def extract_triangle_slice(volume, a, b, c):
    # Returns the 2D image extracted from the volume.
    # Convert each (x, y, z) point into a NumPy array of decimal numbers.
    # This allows vector operations such as b - a and movement between voxels.
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    dab = np.linalg.norm(b - a)  # Distance from a to b.
    dbc = np.linalg.norm(c - b)  # Distance from b to c.

    # We can add a check for dab == 0 before dividing.
    v_ab = (b - a) / dab
    v_ac = (c - a) / dab

    height = int(np.ceil(dab))
    width = int(np.ceil(dbc))
    # We can add one column to include both ends of the base.
    E = np.zeros((height, width))

    a1 = a
    a2 = a

    for y in range(height):
        # We can shorten the last step and use exact endpoints to avoid drift.
        a1 = a1 + v_ab
        a2 = a2 + v_ac

        p = a1
        d12 = np.linalg.norm(a2 - a1) #distance between the progressing a1 and a2

        # We can add a check for d12 == 0 before dividing.
        dp = (a2 - a1) / d12 #vector frop a1 to a2 normalised

        # We can add a small tolerance for floating-point rounding errors.
        for x1 in range(int(np.floor(d12)) + 1):
            value = 0
            # Use the nearest voxel; volume axes are assumed to be (x, y, z).
            if np.all(p >= 0) and np.all(p <= np.array(volume.shape) - 1):
                voxel_index = np.rint(p).astype(int)
                value = volume[tuple(voxel_index)]

            # Convert the output coordinate to an integer index for NumPy.
            x = int((dbc / 2) - (d12 / 2) + x1)
            # We can check that x is within the output image before writing.
            E[y, x] = value
            p = p + dp

    return E
