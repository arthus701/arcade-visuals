import numpy as np
from random_interpolator import RandomInterpolator

bgcolor_span = 100
bgcolor_list = [
    np.array([255, 0, 0]),
    np.array([200, 0, 155]),
    np.array([100, 0, 255]),
    np.array([200, 0, 255]),
    np.array([255, 0, 255]),
    np.array([100, 0, 100]),
]

bgtail_span = 40
bgtail_list = [10, 255, 100, 200]

bgcolorInterpolator = RandomInterpolator(
    bgcolor_span,
    bgcolor_list,
    1,
)

bgtailInterpolator = RandomInterpolator(
    bgtail_span,
    bgtail_list,
    0.5,
)
