import arcade

import time

import numpy as np

from simplex_noise import snoise

import pyaudio

import audioop
from random_interpolator import RandomInterpolator
from parameters import (
    angs,
    form_span,
    form_list,
    bgseed_span,
    bgseed_list,
    bgfreq_span,
    bgfreq_list,
)

rng = np.random.default_rng(1312)


formInterpolator = RandomInterpolator(
    form_span,
    form_list,
    4,
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
        frequency=1/200,
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

CHUNK = 600  # Number of data points to read at a time
RATE = 44100  # Samples per second
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

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

        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)
        self.set_vsync(True)

        arcade.set_background_color(
            (0, 0, 0, 0),
        )

        self.line = np.zeros((2, len(angs)))

        self.pointcloud = PointCloud(5000)

        self.mid_line = np.zeros((2, len(angs)))

        self.high_line = np.zeros((2, len(angs)))

        arcade.enable_timings()


    def on_draw(self):

        self.clear()

        # Get viewport dimensions
        left, screen_width, bottom, screen_height = self.get_viewport()

        width, height = self.get_size()

        arcade.draw_points(
            self.pointcloud.get_coords(width=width, height=height).T,
            (255, 255, 255, 255),
            2,
        )

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
        scale = min(width, height) / 6
        global now
        now = time.time() - starttime
        formInterpolator.update(delta_time)
        bgseedInterpolator.update(delta_time)
        bgfreqInterpolator.update(delta_time)

        arg = np.round(now, 2)

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
        
        self.line = scale * rad * rms_scale * formInterpolator.get() + offset[:, None] 

        self.mid_line = scale * rad_mid * rms_scale * formInterpolator.get() + offset[:, None]

        self.high_line = scale * rad_high * rms_scale * formInterpolator.get() + offset[:, None]

        self.pointcloud.coords += \
            grad(self.pointcloud.get_coords(width, height)) * delta_time

def main():
    """ Main function """
    MyGame()
    arcade.run()
    stream.close()


if __name__ == "__main__":
    main()
