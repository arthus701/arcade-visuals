import numpy as np


def ngon_polar(ang, angs):
    # n_points = 3

    _angs = np.hstack(
        [
            # angs[0],
            angs,
            360 + angs[0],
            # 360 + angs[0],
        ]
    )
    points = np.array(
        [
            np.cos(np.deg2rad(_angs)),
            np.sin(np.deg2rad(_angs)),
        ]
    )
    return np.array(
        [
            np.interp(ang, _angs, points[0]),
            np.interp(ang, _angs, points[1]),
        ],
    )
