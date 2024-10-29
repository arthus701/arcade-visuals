import numpy as np

import arcade
from simplex_noise import snoise
from random_interpolator import RandomInterpolator
from state import State

from background import bgcolorInterpolator, bgtailInterpolator


bgseed_list = [
    66359,  23802,  72212,  87422,  93711,  60901, 102507,  86383,
    85871,  29174,  67382,  31268,  49904,  46217,  36448,   4085,
    83402, 100324,  38140,  45713,  43896,  16853,  86778,   3440,
    76750,  14508,  19974,  87937,  25580,  49236,  14495,  41940,
    69652,  15417,  50981,  73977,  74383,  48582,  54104,  45674,
    99805,   3940,  14555,  59095,  44172,  42904,  50004,  68999,
    9507,  87843, 100043,  88797,  74890,  60940,  53515,  51485,
    10603,  57034,  89593,  54704,  50310,  70297,  36594,  41455,
    71175,  16918,  18941,  16480,  69407,  98259,  66323,  60134,
    55220,  74973,  40513,  68977,  58235,  51438,  10734,  22637,
    19618,  78404,  52584,  33885,  88093,  43323,  49493,  95712,
    96190,  27274,  95760,  15794,  11261,  16946,  12098,  48366,
    100148,  14988,  76259,  53729,
]

seedInterpolator = RandomInterpolator(
    30,
    bgseed_list,
    0,
)

freqInterpolator = RandomInterpolator(
    200,
    [1/200, 1/100, 1/500, 1/10],
    0.3,
)

rng = np.random.default_rng()


def curl_func(coords, add_freq=0):
    res = 1 * snoise(
        coords,
        octaves=4,
        frequency=freqInterpolator.get()+add_freq,
        seed=int(seedInterpolator.get()),
    )
    return res


def grad(y, h=1e-2, add_freq=0):
    ret = np.zeros((2, y.shape[1]))
    vec = np.zeros((3, y.shape[1]))
    vec[:2] = y

    for it in range(2):
        dir = np.zeros(3)
        dir[it] = 1.

        pfield = curl_func((vec + dir[:, None] * h), add_freq=add_freq)
        nfield = curl_func((vec - dir[:, None] * h), add_freq=add_freq)
        ret[it] = ((pfield - nfield) / (2 * h))

    curl = np.array(
        [
            ret[1],
            -ret[0],
        ],
    )
    return curl


class PointCloud(State):
    def __init__(self, n=10):
        self.n = n

        self.background_intensity = 1

        self.coords = rng.uniform(size=(2, self.n))
        self.colors = rng.integers(low=0, high=255, size=(3, self.n))

        self.add_freq = 0

    def get_coords(self, width, height):
        return (
            self.coords * np.array([width, height])[:, None]
            % np.array([width, height])[:, None]
        )

    def update_window(self, width, height, **kwargs):
        pass

    def update(self, elapsed_time, delta_time, **kwargs):
        if 'rms_buffer' in kwargs:
            rms_buffer = kwargs.get('rms_buffer')
            self.background_intensity = 1 - np.clip(
                10 * (
                    (np.max(rms_buffer[:3]) - np.mean(rms_buffer[:3]))
                    / (np.max(rms_buffer) + 1e-10)
                ),
                None,
                1,
            )
        if 'kick' in kwargs:
            kick = kwargs.get('kick')
            if kick:
                self.add_freq += 0.05

        seedInterpolator.update(delta_time)
        freqInterpolator.update(delta_time)
        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)

        width, height = arcade.get_window().get_size()
        self.coords += (
            grad(self.get_coords(width, height), add_freq=self.add_freq)
            * delta_time
        )

        self.add_freq = np.clip(self.add_freq - 0.005, 0., 0.8)

    def draw(self, width, height, **kwargs):
        bgcolor = bgcolorInterpolator.get()
        arcade.draw_rectangle_filled(
            width // 2,
            height // 2,
            width,
            height,
            color=(
                bgcolor[0] * (0.1 + 0.9 * self.background_intensity),
                bgcolor[1] * (0.1 + 0.9 * self.background_intensity),
                bgcolor[2] * (0.1 + 0.9 * self.background_intensity),
                bgtailInterpolator.get(),
            ),
        )

        arcade.draw_points(
            self.get_coords(width=width, height=height).T,
            arcade.color.WHITE,
            2,
        )
