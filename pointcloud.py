import numpy as np

import arcade
from simplex_noise import snoise
from random_interpolator import RandomInterpolator
from state import State

from parameters import (
    bgseed_span,
    bgseed_list,
    bgfreq_span,
    bgfreq_list,
)

seedInterpolator = RandomInterpolator(
    bgseed_span,
    bgseed_list,
    0,
)

freqInterpolator = RandomInterpolator(
    bgfreq_span,
    bgfreq_list,
    0.3,
)

rng = np.random.default_rng()


def curl_func(coords):
    res = 1 * snoise(
        coords,
        octaves=4,
        frequency=freqInterpolator.get(),
        seed=int(seedInterpolator.get()),
    )
    return res


def grad(y, h=1e-2):
    ret = np.zeros((2, y.shape[1]))
    vec = np.zeros((3, y.shape[1]))
    vec[:2] = y

    for it in range(2):
        dir = np.zeros(3)
        dir[it] = 1.

        pfield = curl_func((vec + dir[:, None] * h))
        nfield = curl_func((vec - dir[:, None] * h))
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

        self.coords = rng.uniform(size=(2, self.n))
        self.colors = rng.integers(low=0, high=255, size=(3, self.n))

    def get_coords(self, width, height):
        return (
            self.coords * np.array([width, height])[:, None]
            % np.array([width, height])[:, None]
        )

    def update_window(self, width, height):
        pass

    def update(self, elapsed_time, delta_time):
        seedInterpolator.update(delta_time)
        freqInterpolator.update(delta_time)

        width, height = arcade.get_window().get_size()
        self.coords += \
            grad(self.get_coords(width, height)) * delta_time

    def draw(self, width, height):
        arcade.draw_points(
            self.get_coords(width=width, height=height).T,
            arcade.color.WHITE,
            2,
        )
