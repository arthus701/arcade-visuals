import numpy as np

import arcade
from PIL import Image
from matplotlib import cm

from simplex_noise import snoise
from state import State


def func(coords, seed=161312, z=0, exp=1):
    _coords = coords.T
    _coords = np.vstack(
        (
            _coords,
            z * np.ones((1, _coords.shape[1]))
        ),
    )

    res = (
        snoise(
            _coords,
            octaves=3,
            frequency=4,
            seed=seed,
        ),
        #  * snoise(
        #    _coords,
        #    frequency=20,
        #    octaves=8,
        #    seed=seed+4,
        # )
    )

    # res -= res.min()
    # res /= np.max(np.abs(res))

    res *= np.exp(
        -np.sqrt(
            (
                (_coords[0])**2 + (_coords[1])**2
            ) / .1
        )**(3 + 3.2*exp)
    )

    # res -= res.min()
    res /= np.max(np.abs(res))

    # res = 1 - res
    res = np.round(res, 1)

    return res


class Sun(State):
    def __init__(self, extent, subsamp=10):
        self.width, self.height = arcade.get_window().get_size()
        self.extent = (0, 0, self.width, self.height)

        self.glow_max = 0.8

        X, Y = np.meshgrid(
            1.*np.arange(
                self.width+subsamp,
                step=subsamp,
            ),
            1.*np.arange(
                self.height+subsamp,
                step=subsamp,
            ),
            indexing='xy',
        )
        xy_grid = np.concatenate(
            (
                X.T[..., None],
                Y.T[..., None],
            ),
            axis=-1,
        )
        self.n_x = xy_grid.shape[0]
        self.n_y = xy_grid.shape[1]
        self.xy_grid = xy_grid.reshape(self.n_x*self.n_y, 2)

        self.xy_grid[:, 0] = (
            self.xy_grid[:, 0] - self.width / 2
        ) / min(self.width, self.height)
        self.xy_grid[:, 1] = (
            self.height / 2 - self.xy_grid[:, 1]
        ) / min(self.width, self.height)

        self.texture_atlas = arcade.TextureAtlas(
            size=(self.n_x, self.n_y),
        )

        self.texture = arcade.Texture(
            'main',
            hit_box_algorithm='None',
        )
        self.update(0, 0)
        self.texture_atlas.add(self.texture)

        self.sprite_list = arcade.SpriteList(
            atlas=self.texture_atlas,
        )
        self.sprite = arcade.Sprite(
            scale=subsamp,
            center_x=self.width // 2,
            center_y=self.height // 2,
            image_width=self.width,
            image_height=self.height,
            texture=self.texture,
            hit_box_algorithm='None',
            angle=0,
        )
        self.sprite_list.append(
            self.sprite
        )

    def update_window(self, width, height, **kwargs):
        pass

    def draw(self, width, height, **kwargs):
        self.sprite_list.draw(pixelated=True)
        # self.sprite.draw()
        # arcade.draw_texture_rectangle(
        #     (self.extent[0] + self.extent[2]) // 2,
        #     (self.extent[1] + self.extent[3]) // 2,
        #     self.width,
        #     self.height,
        #     self.texture_atlas.texture,
        # )
        self.texture_atlas.update_texture_image(self.texture)

    def update(self, elapsed_time, delta_time, **kwargs):
        if 'rms_buffer' in kwargs:
            rms_buffer = kwargs.get('rms_buffer')
            exp_add = 1 - np.clip(
                10 * (
                    (np.max(rms_buffer[:3]) - np.mean(rms_buffer[:3]))
                    / (np.max(rms_buffer) + 1e-10)
                ),
                None,
                1,
            )
        else:
            exp_add = 0
        if 'kick' in kwargs:
            kick = kwargs.get('kick')
            if kick:
                self.glow_max += 0.5

        arg = np.round(elapsed_time, 2)
        self.vals = func(
            self.xy_grid,
            z=0.05*arg,
            exp=exp_add,
        ).reshape(self.n_x, self.n_y)

        self.image = Image.fromarray(
            # np.uint8(255 * self.vals).T,
            np.uint8(cm.magma(self.vals.T * self.glow_max) * 255),
        )
        self.texture.image = self.image

        self.glow_max = np.clip(self.glow_max - 0.05, 0.5, 1.)
