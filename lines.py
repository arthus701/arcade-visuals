import numpy as np

import arcade

from matplotlib import cm

from simplex_noise import snoise
from state import State

from background import bgcolorInterpolator, bgtailInterpolator


def curl_func(coords, z=0, add_freq=0):
    res = 1 * snoise(
        np.vstack(
            [
                coords,
                z*np.ones(coords.shape[1])[None, :],
            ],
        ),
        octaves=4,
        frequency=5+add_freq,
        seed=189,
    )
    return res


class Lines(State):
    def __init__(self, n_x=10, n_y=10, res=100):
        self.n_x = int(n_x)
        self.n_y = int(n_y)
        self.res = int(res)

        lines = []
        xtnd = 0.9
        for n in np.linspace(-xtnd, xtnd, n_x):
            lines.append(
                np.array(
                    [
                        n*np.ones(res),
                        np.linspace(-xtnd, xtnd, res),
                    ]
                )
            )
        for n in np.linspace(-xtnd, xtnd, n_y):
            lines.append(
                np.array(
                    [
                        np.linspace(-xtnd, xtnd, res),
                        n*np.ones(res),
                    ]
                )
            )

        self.lines = np.hstack(
            lines,
        )

        self.add_z = 0

    def coords_to_pixels(self, width, height, coords):
        which = min(width, height) // 2
        return (
            coords * np.array([which, which])[:, None]
            + np.array([width // 2, height // 2])[:, None]
        )

    def update(self, elapsed_time, delta_time, **kwargs):
        if 'kick' in kwargs:
            kick = kwargs.get('kick')
            if kick:
                self.add_z += 1

        angles = curl_func(
            self.lines,
            z=elapsed_time % 400,
            add_freq=10*self.add_z,
        )
        self.lines += 0.1 * delta_time * np.array(
            [
                np.cos(2 * np.pi * angles),
                np.sin(2 * np.pi * angles),
            ],
        )
        self.lines -= np.mean(self.lines, axis=1)[:, None]

        self.add_z = np.clip(self.add_z - 0.05, 0., None)
        print(self.add_z)

    def draw(self, width, height, **kwargs):
        bgcolor = bgcolorInterpolator.get()
        arcade.draw_rectangle_filled(
            width // 2,
            height // 2,
            width,
            height,
            color=(
                0,
                bgcolor[1],
                bgcolor[2],
                255,
            ),
        )

        for n in range(self.n_x + self.n_y):
            line = self.lines[:, n * self.res:(n+1)*self.res]
            pixels = self.coords_to_pixels(
                width, height, line,
            ).T

            # arcade.draw_points(
            #     pixels[::10],
            #     arcade.color.WHITE,
            #     10,
            # )

            color = np.array(cm.viridis(n / (self.n_x + self.n_y))) * 255
            arcade.draw_line_strip(
                pixels,
                (int(color[0]), int(color[1]), int(color[2]), 255),
                2,
            )
