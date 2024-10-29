import numpy as np
import arcade

from state import State

from background import bgcolorInterpolator, bgtailInterpolator


rng = np.random.default_rng(seed=161)


class Ferris(State):
    def __init__(self, n=10, center=(0, 0)):
        self.n = n
        self.angles = np.unique(
            rng.uniform(0, 2*np.pi, size=n),
        )
        self.angles = np.concatenate(
            (
                self.angles,
                [self.angles[0]],
            ),
        )
        self.radii = 0.7 * np.ones(n) + 0.2 * np.random.uniform(size=n)
        self.center = center

    def coords_to_pixels(self, width, height, coords):
        which = min(width, height) // 2
        return (
            coords * np.array([which, which])[:, None]
            + np.array([width // 2, height // 2])[:, None]
        )

    def get_triangles(self):
        triangles = []
        for it in range(len(self.angles)-1):
            triangles.append(
                [
                    self.center,
                    (
                        self.center[0] + self.radii[it]
                        * np.cos(self.angles[it]),
                        self.center[1] + self.radii[it]
                        * np.sin(self.angles[it]),
                    ),
                    (
                        self.center[0] + self.radii[it]
                        * np.cos(self.angles[it+1]),
                        self.center[1] + self.radii[it]
                        * np.sin(self.angles[it+1]),
                    ),
                ],
            )

        return triangles

    def update(self, elapsed_time, delta_time, **kwargs):
        # if 'rms_buffer' in kwargs:
        #     rms_buffer = kwargs.get('rms_buffer')

        if 'kick' in kwargs:
            kick = kwargs.get('kick')
            if kick:
                self.n += 1 * np.random.choice((-1, 1))
                self.n = max(3, self.n)
                self.__init__(n=self.n)

        self.radii = self.radii

        bgtailInterpolator.update(delta_time)

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
                bgtailInterpolator.get(),
            ),
        )

        for triangle in self.get_triangles():
            pixels = self.coords_to_pixels(
                width, height, np.array(triangle).T,
            ).T
            arcade.draw_triangle_outline(
                *pixels[0],
                *pixels[1],
                *pixels[2],
                color=arcade.color.WHITE,
            )
