# The first version of the algorithm, one pixel at a time, kept as a reference.
# It follows the professor's pseudo-code line by line, so it is easy to check by hand,
# but it is too slow (about 1 image per second on MRHead).
# tests/test_fast_matches_slow.py checks that slicing.extract_slice gives the same images.

import numpy as np

from slicing import TINY, check_shape, image_size, length


def slow_extract_slice(volume, a1, a2, b, c):
    a1, a2, b, c, dab, dbc = check_shape(a1, a2, b, c)

    v_ab = (b - a1) / dab
    v_ac = (c - a2) / dab

    height, width = image_size(dab, dbc)
    E = np.zeros((height, width), dtype=volume.dtype)

    # a1 and a2 start at the given points (both at a for a triangle).
    start1 = a1
    start2 = a2

    for y in range(height):
        # Step from the start points, the last step is shorter (see slicing.py).
        step = min(y + 1, dab)
        a1 = start1 + step * v_ab
        a2 = start2 + step * v_ac

        d12 = length(a2 - a1)  # distance between the progressing a1 and a2
        d12 = min(d12, dbc)  # a row is never wider than the base
        dp = (a2 - a1) / d12  # vector from a1 to a2 normalised

        for x1 in range(int(np.floor(d12 + TINY)) + 1):
            p = a1 + x1 * dp
            value = 0
            if np.all(p >= 0) and np.all(p <= np.array(volume.shape) - 1):  # inside the volume
                # Round to the nearest voxel; .5 always goes up (p >= 0 here).
                voxel_index = np.floor(p + 0.5).astype(int)
                value = volume[tuple(voxel_index)]

            x = int((dbc / 2) - (d12 / 2) + x1)
            E[y, x] = value

    return E
