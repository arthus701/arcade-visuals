import arcade

import numpy as np
from background import bgcolorInterpolator, bgtailInterpolator


class State(object):
    def __init__(self, *args, **kwargs):
        pass

    def update(self, elapsed_time, delta_time, **kwargs):
        pass

    def update_window(self, *args, **kwargs):
        pass

    def draw(self, width, height, **kwargs):
        pass


class InitialState(State):
    def __init__(self, *args, **kwargs):
        self.background_intensity = 1

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

        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)

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

        width, height = arcade.get_window().get_size()
        arcade.draw_text(
            "Select state using the number keys.\n"
            "1: Sun\n"
            "2: Point cloud\n"
            "3: Ferris\n"
            "4: Lines",
            0,
            2*height//3,
            width=width,
            align="center"
        )
