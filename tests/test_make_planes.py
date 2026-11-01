# The plane generator: python make_planes.py file.nrrd file.csv
# The CSV it writes must be read back by Ex0.py, row by row, with valid shapes.

import nrrd
import numpy as np
import pytest

import make_planes
from Ex0 import read_planes
from slicing import check_shape, four_points


@pytest.mark.parametrize("mode", ["rotate", "random"])
def test_written_csv_is_read_back_by_ex0(tmp_path, mode):
    nrrd_path = tmp_path / "volume.nrrd"
    nrrd.write(str(nrrd_path), np.zeros((30, 40, 20), dtype=np.uint8), index_order="F")
    csv_path = tmp_path / "planes.csv"

    make_planes.main([str(nrrd_path), str(csv_path), "--count", "12", "--mode", mode])

    planes = read_planes(csv_path)
    assert len(planes) == 12
    for row_number, points in planes:
        check_shape(*four_points(points))  # 6 decimals keep the sides equal within EPS
