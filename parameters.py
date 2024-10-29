import numpy as np

from ngon_polar import ngon_polar

num_points = 5000
ang_reso = 1001
angs = np.linspace(0, 360, ang_reso)
# -----------------------------------------------------------------------------
# central shapes
form_span = 3

form_1 = [
    0,
    150,
    270,
]

form_2 = [
    0,
    90,
    180,
    270,
]

form_list = [
    ngon_polar(angs, form_1),
    ngon_polar(angs, form_2),
    np.array(
        [
            np.cos(np.deg2rad(angs)),
            np.sin(np.deg2rad(angs)),
        ]
    )
]


formfreq_span = 200
formfreq_list = [1/200, 1/100, 1/500, 1/10]

add_span = 20
add_list = [1., 0.5, 0.1]

mul_span = 26
mul_list = [1., 0.5, 0.1]
