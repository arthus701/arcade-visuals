import arcade
import time
import argparse

import numpy as np

from simplex_noise import snoise

from lib.audio_client import AudioClient
from lib.parameters_client import (ParametersClient, default_parameters)
from lib.ngon_polar import ngon_polar
from lib.point_cloud import PointCloud
from lib.random_interpolator import RandomInterpolator
from lib.utils import (func, grad)

# parse cli args
parser = argparse.ArgumentParser()
parser.add_argument('--audio_client_port', type=int, default=46498)
parser.add_argument('--parameters_client_port', type=int, default=46499)

args = parser.parse_args()

# initialize Random Interpolators
rng = np.random.default_rng(1312)

form_list = lambda params: [
    ngon_polar(params.angs, params.form_1),
    ngon_polar(params.angs, params.form_2),
    np.array(
        [
            np.cos(np.deg2rad(params.angs)),
            np.sin(np.deg2rad(params.angs)),
        ]
    )
]

formfreqInterpolator = RandomInterpolator(
    default_parameters.formfreq_span,
    default_parameters.formfreq_list,
    0.3,
)

addInterpolator = RandomInterpolator(
    default_parameters.add_span,
    default_parameters.add_list,
    4,
)

mulInterpolator = RandomInterpolator(
    default_parameters.mul_span,
    default_parameters.mul_list,
    4,
)

formInterpolator = RandomInterpolator(
    default_parameters.form_span,
    form_list(default_parameters),
    4,
)

bgcolorInterpolator = RandomInterpolator(
    default_parameters.bgcolor_span,
    default_parameters.bgcolor_list,
    1,
)

bgtailInterpolator = RandomInterpolator(
    default_parameters.bgtail_span,
    default_parameters.bgtail_list,
    0.5,
)

bgseedInterpolator = RandomInterpolator(
    default_parameters.bgseed_span,
    default_parameters.bgseed_list,
    0,
)

bgfreqInterpolator = RandomInterpolator(
    default_parameters.bgfreq_span,
    default_parameters.bgfreq_list,
    0.3,
)

starttime = time.time()
now = 0

class Visuals(arcade.Window):
    """ Main application class. """

    def __init__(self):
        super().__init__(
            800,
            600,
            "Animation",
            fullscreen=False,
            vsync=True,
        )

        self.audio_client = AudioClient("0.0.0.0", args.audio_client_port, 1024)
        self.parameters_client = ParametersClient("0.0.0.0", args.parameters_client_port, 1024)
        self.parameters = self.parameters_client.update()

        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)

        arcade.set_background_color(
            (0, 0, 0, 0),
        )

        self.line = np.zeros((2, self.parameters.ang_reso))

        self.mid_line = np.zeros((2, self.parameters.ang_reso))

        self.high_line = np.zeros((2, self.parameters.ang_reso))

        self.pointcloud = PointCloud(rng, self.parameters.num_points)

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
        ang = arg / self.parameters.ang_arg_div * np.ones(self.line.shape[1])
        rotmat = np.array(
            [
                [np.cos(ang), np.sin(ang)],
                [-np.sin(ang), np.cos(ang)],
            ]
        )
        rad = np.array(
            [
                np.ones(self.parameters.ang_reso),
                addInterpolator.get()
                + mulInterpolator.get() 
                * func(self.line, now, formfreqInterpolator.get()),
            ]
        )

        # XXX READING HERE
        try:
            data = self.audio_client.update()

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

        rad_mid = rms_val * 400 + np.mean(self.mid_buffer) * 200
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
            grad(self.pointcloud.get_coords(width, height), bgfreqInterpolator.get(), bgseedInterpolator.get()) \
            * delta_time

        self.mid_line = (1 + rad_mid) * line + offset[:, None]
        self.high_line = (1 - rad_high) * line + offset[:, None]

        ### Update Parameters
        self.parameters = self.parameters_client.update()
        
        self.pointcloud.n = self.parameters.num_points
        formInterpolator.span = self.parameters.form_span
        formInterpolator.statelist = form_list(self.parameters)

        print(self.parameters.num_points)


def main():
    """ Main function """
    Visuals()
    arcade.run()


if __name__ == "__main__":
    main()
