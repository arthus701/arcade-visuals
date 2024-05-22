import arcade

import time

import numpy as np

from simplex_noise import snoise


rng = np.random.default_rng(1312)


def func(coords, seed=141):
    global TIME

    _coords = np.vstack(
        (
            coords,
            TIME * np.ones((1, coords.shape[1])) * 100,
        ),
    )
    res = snoise(
        _coords,
        octaves=6,
        frequency=1 / 200,
        seed=seed,
    )
    res /= np.max(np.abs(res))
    return (res + 1) / 2


def ngon_polar(ang, angs):
    # n_points = 3

    _angs = np.hstack(
        [
            # angs[0],
            angs,
            360 + angs[0],
            # 360 + angs[0],
        ]
    )
    points = np.array(
        [
            np.cos(np.deg2rad(_angs)),
            np.sin(np.deg2rad(_angs)),
        ]
    )
    return np.array(
        [
            np.interp(ang, _angs, points[0]),
            np.interp(ang, _angs, points[1]),
        ],
    )


TIME = 0
INTERPOLATE_TIME = 0
STARTTIME = time.time()

INTERPOLATE_SPAN = 3
ANGS = np.linspace(0, 360, 401)
SCALE = 200

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Full Screen Example"

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
MOVEMENT_SPEED = 5

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

formlist = [
    ngon_polar(ANGS, form_1),
    ngon_polar(ANGS, form_2),
    np.array(
        [
            np.cos(np.deg2rad(ANGS)),
            np.sin(np.deg2rad(ANGS)),
        ]
    )
]


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self):
        """
        Initializer
        """
        # Open a window in full screen mode. Remove fullscreen=True if
        # you don't want to start this way.
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE,
            fullscreen=False,
        )

        # This will get the size of the window, and set the viewport to match.
        # So if the window is 1000x1000, then so will our viewport. If
        # you want something different, then use those coordinates instead.
        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)
        self.set_vsync(True)

        arcade.set_background_color(
            # (100, 0, 200, 100),
            (0, 0, 0, 0),
        )

        self.new_form = formlist[0]
        self.old_form = self.new_form.copy()

        self.line = np.zeros((2, len(ANGS)))

    def on_draw(self):
        """
        Render the screen.
        """

        self.clear(
            # (100, 0, 200, 100)
        )

        # Get viewport dimensions
        left, screen_width, bottom, screen_height = self.get_viewport()

        # text_size = 18
        # Draw text on the screen so the user has an idea of what is happening
        # arcade.draw_text(
        #     "Press F to toggle between full screen and "
        #     "windowed mode, unstretched.",
        #     screen_width // 2, screen_height // 2 - 20,
        #     arcade.color.WHITE, text_size, anchor_x="center"
        #     )

        width, height = self.get_size()

        arcade.draw_line_strip(
            self.line.T,
            arcade.color.WHITE,
            3,
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
        width, height = self.get_size()
        global TIME, INTERPOLATE_TIME, INTERPOLATE_SPAN
        TIME = time.time() - STARTTIME
        # if TIME %
        INTERPOLATE_TIME += delta_time / INTERPOLATE_SPAN
        if 1. < INTERPOLATE_TIME:
            INTERPOLATE_TIME -= 1
            self.old_form = self.new_form.copy()
            idx = rng.integers(len(formlist))
            # print(idx)
            self.new_form = formlist[idx]

        arg = np.round(TIME, 2)

        rad = np.array(
            [
                np.cos(arg) * np.ones(self.line.shape[1]),
                1. + 0.4 * func(self.line),
            ],
        )
        # rad = 1.

        offset = np.array(
            [
                width // 2,
                height // 2,
            ]
        )
        exp = 4
        self.line = SCALE * rad * (
            (1 - INTERPOLATE_TIME**exp) * self.old_form
            + INTERPOLATE_TIME**exp * self.new_form
        ) + offset[:, None]


def main():
    """ Main function """
    MyGame()
    arcade.run()


if __name__ == "__main__":
    main()
