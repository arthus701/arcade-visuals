import arcade
import socket
import time
import json

import numpy as np

from simplex_noise import snoise


from random_interpolator import RandomInterpolator
from parameters import (
    num_points,
    ang_reso,
    form_span,
    form_list,
    formfreq_span,
    formfreq_list,
    add_span,
    add_list,
    mul_span,
    mul_list,
    bgcolor_span,
    bgcolor_list,
    bgtail_span,
    bgtail_list,
    bgseed_span,
    bgseed_list,
    bgfreq_span,
    bgfreq_list,
)


rng = np.random.default_rng(1312)


formfreqInterpolator = RandomInterpolator(
    formfreq_span,
    formfreq_list,
    0.3,
)

addInterpolator = RandomInterpolator(
    add_span,
    add_list,
    4,
)

mulInterpolator = RandomInterpolator(
    mul_span,
    mul_list,
    4,
)

formInterpolator = RandomInterpolator(
    form_span,
    form_list,
    4,
)

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

bgseedInterpolator = RandomInterpolator(
    bgseed_span,
    bgseed_list,
    0,
)

bgfreqInterpolator = RandomInterpolator(
    bgfreq_span,
    bgfreq_list,
    0.3,
)

starttime = time.time()
now = 0


def func(coords, seed=141):
    global now

    _coords = np.vstack(
        (
            coords,
            now * np.ones((1, coords.shape[1])) * 100,
        ),
    )
    res = snoise(
        _coords,
        octaves=6,
        frequency=formfreqInterpolator.get(),
        seed=seed,
    )
    res /= np.max(np.abs(res))
    return (res + 1) / 2


def curl_func(coords):
    res = 1 * snoise(
        coords,
        octaves=4,
        frequency=bgfreqInterpolator.get(),
        seed=int(bgseedInterpolator.get()),
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


class PointCloud(object):
    def __init__(self, n=10):
        self.n = n

        self.coords = rng.uniform(size=(2, self.n))
        self.colors = rng.integers(low=0, high=255, size=(3, self.n))

    def get_coords(self, width, height):
        return (
            self.coords * np.array([width, height])[:, None]
            % np.array([width, height])[:, None]
        )


PORT = 46498


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self):
        super().__init__(
            800,
            600,
            "Animation",
            fullscreen=False,
            vsync=True,
        )

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )
        self.socket.bind(("0.0.0.0", PORT))
        self.socket.setblocking(0)

        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)

        arcade.set_background_color(
            (0, 0, 0, 0),
        )

        self.line = np.zeros((2, ang_reso))

        self.mid_line = np.zeros((2, ang_reso))

        self.high_line = np.zeros((2, ang_reso))

        self.pointcloud = PointCloud(num_points)

        buffersize = 3
        self.low_buffer = np.zeros(buffersize)
        self.mid_buffer = np.zeros(buffersize)
        self.high_buffer = np.zeros(buffersize)

        self.rms_buffer = np.zeros(buffersize)

        arcade.enable_timings()

    def on_draw(self):

        # self.clear()

        # Get viewport dimensions
        left, screen_width, bottom, screen_height = self.get_viewport()

        width, height = self.get_size()

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
            self.pointcloud.get_coords(width=width, height=height).T,
            arcade.color.WHITE,
            2,
        )

        arcade.draw_points(
            self.line.T[::50],
            arcade.color.WHITE,
            10,
        )

        arcade.draw_line_strip(
            self.line.T,
            arcade.color.WHITE,
            2,
        )

        arcade.draw_line_strip(
            self.mid_line.T,
            arcade.color.WHITE,
            3
        )

        arcade.draw_line_strip(
            self.high_line.T,
            arcade.color.WHITE,
            3
        )

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        if key == arcade.key.F:
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            # Get the window coordinates. Match viewport to window coordinates
            # so there is a one-to-one mapping.
            width, height = self.get_size()
            self.set_viewport(0, width, 0, height)

    def on_update(self, delta_time):
        # print(arcade.get_fps())
        width, height = self.get_size()
        scale = min(width, height) / 6
        global now
        now = time.time() - starttime
        formInterpolator.update(delta_time)
        addInterpolator.update(delta_time)
        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)
        bgseedInterpolator.update(delta_time)
        bgfreqInterpolator.update(delta_time)

        arg = np.round(now, 2)
        ang = arg / 20 * np.ones(self.line.shape[1])
        rotmat = np.array(
            [
                [np.cos(ang), np.sin(ang)],
                [-np.sin(ang), np.cos(ang)],
            ]
        )
        rad = np.array(
            [
                np.ones(ang_reso),
                addInterpolator.get()
                + mulInterpolator.get() * func(self.line),
            ]
        )
        # XXX READING HERE
        try:
            while True:
                raw_data = self.socket.recv(1024)
        except BlockingIOError:
            pass

        try:
            data = json.loads(raw_data)

            low_c = data['low_peak']['amp']
            low_c_norm = np.clip(low_c, None, 6e6) / 6e6

            self.low_buffer[1:] = self.low_buffer[:-1]
            self.low_buffer[0] = low_c_norm

            mid_c = data['mid_peak']['amp']
            mid_c_norm = np.clip(mid_c, None, 6e6) / 6e6

            self.mid_buffer[1:] = self.mid_buffer[:-1]
            self.mid_buffer[0] = mid_c_norm

            high_c = data['high_peak']['amp']
            high_c_norm = np.clip(high_c, None, 6e6) / 6e6

            self.high_buffer[1:] = self.high_buffer[:-1]
            self.high_buffer[0] = high_c_norm

            rms = data['rms']
            rms_norm = np.clip(rms, None, 1e4) / 1e4

            self.rms_buffer[1:] = self.rms_buffer[:-1]
            self.rms_buffer[0] = rms_norm
        except UnboundLocalError:
            pass

        self.background_intensity = np.mean(self.low_buffer)

        rms_val = self.rms_buffer.mean()

        rad_mid = rms_val * 400 + np.mean(self.mid_buffer) * 100
        rad_high = rms_val * 10 + np.mean(self.high_buffer) * 4

        # rad = 1.

        offset = np.array(
            [
                width // 2,
                height // 2,
            ]
        )

        line = np.einsum(
            'ijk, jk->ik',
            scale * rotmat,
            rad,
        ) * formInterpolator.get()

        self.line = line + offset[:, None]

        self.pointcloud.coords += \
            grad(self.pointcloud.get_coords(width, height)) * delta_time

        self.mid_line = (1 + rad_mid) * line + offset[:, None]
        self.high_line = (1 - rad_high) * line + offset[:, None]

        # self.high_line = (
        #     scale * rad_high * rms_scale * formInterpolator.get()
        #     + offset[:, None]
        # )


def main():
    """ Main function """
    MyGame()
    arcade.run()


if __name__ == "__main__":
    main()
