import numpy as np
from random_interpolator import RandomInterpolator

bgcolor_list = [
    np.array([255, 0, 0]),
    np.array([200, 0, 155]),
    np.array([100, 0, 255]),
    np.array([200, 0, 255]),
    np.array([255, 0, 255]),
    np.array([100, 0, 100]),
]

bgcolorInterpolator = RandomInterpolator(
    100,
    bgcolor_list,
    1,
)

bgtailInterpolator = RandomInterpolator(
    40,
    [10, 255, 100, 200],
    0.5,
)
