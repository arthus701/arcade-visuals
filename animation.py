import arcade

import time

import numpy as np

from simplex_noise import snoise

import pyaudio

import audioop

rng = np.random.default_rng(1312)


def func(coords, seed=9999, freq=0.005):
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

def categorize_audio_freqs(freqs, fft_data):
    low = mid = high = low_c = mid_c = high_c = 1
    i = 0
    for freq in freqs:
        freq = abs(freq * 11025.0)
        if freq <= 0:
            continue

        fftp = fft_data[i].real
        if freq <= 200 and fftp > low_c:
            low = freq
            low_c = fftp
        elif 200 < freq <= 2000 and fftp > mid_c:
            mid = freq
            mid_c = fftp
        elif 2000 < freq <= 20000 and fftp > high_c:
            high = freq
            high_c = fftp
        
        i = i + 1
    
    return [[low, mid, high], [low_c, mid_c, high_c]]


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

CHUNK = 600  # Number of data points to read at a time
RATE = 44100  # Samples per second
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

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
            vsync=True,
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

        self.mid_line = np.zeros((2, len(ANGS)))

        self.high_line = np.zeros((2, len(ANGS)))

        arcade.enable_timings()


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
            arcade.color.YELLOW,
            5,
        )

        arcade.draw_line_strip(
            self.mid_line.T,
            arcade.color.BLUE,
            3
        )

        arcade.draw_line_strip(
            self.high_line.T,
            (58, 219, 0),
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
        print(arcade.get_fps())
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

        buffer_data = stream.read(CHUNK)

        rms = audioop.rms(buffer_data, 2)  # Calculate the RMS value of each chunk to measure the volume in real time

        data = np.frombuffer(buffer_data, dtype=np.int16)
        # Apply FFT to the audio data to analyze frequency components
        fft_data = np.fft.fft(data)
        frequencies = np.fft.fftfreq(len(fft_data), d=0.1)
        freqs_cat = categorize_audio_freqs(frequencies, fft_data)

        if rms < 500:
            rms_eval = 0
        else:
            rms_eval = rms / 1000

        arcade.set_background_color(
            (min((rms_eval * 100), 200), min((rms_eval * 10), 200), min((rms_eval * 10), 200))
        )

        rad = np.array(
            [
                np.cos(arg) * np.ones(self.line.shape[1]) * (freqs_cat[0][0] / 100),
                1. + 0.2 * func(self.line) * (freqs_cat[1][0]),
            ],
        )

        rad_mid = np.array(
            [
                np.cos(arg) * np.ones(self.mid_line.shape[1]) * (freqs_cat[0][1] / 100),
                1. + 0.2 * func(self.mid_line) * (freqs_cat[1][1] / 100000),
            ],
        )

        rad_high = np.array(
            [
                np.cos(arg) * np.ones(self.high_line.shape[1]) * (freqs_cat[0][2] / 1000),
                1. + 0.2 * func(self.high_line) * (freqs_cat[1][2] / 100000),
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
        rms_scale = min(rms_eval, 0.9)
        if rms_eval == 0:
            rms_scale = 0.1
        
        self.line = SCALE * rad * rms_scale * (
            (1 - INTERPOLATE_TIME**exp) * self.old_form
            + INTERPOLATE_TIME**exp * self.new_form
        ) + offset[:, None] 

        self.mid_line = SCALE * rad_mid * rms_scale * (
            (1 - INTERPOLATE_TIME**exp) * self.old_form
            + INTERPOLATE_TIME**exp * self.new_form
        ) + offset[:, None]

        self.high_line = SCALE * rad_high * rms_scale * (
            (1 - INTERPOLATE_TIME**exp) * self.old_form
            + INTERPOLATE_TIME**exp * self.new_form
        ) + offset[:, None]


def main():
    """ Main function """
    MyGame()
    arcade.run()
    stream.close()


if __name__ == "__main__":
    main()
