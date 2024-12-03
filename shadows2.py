import arcade.color
import arcade.color
import arcade.color
import arcade.color
import numpy as np

import arcade
from simplex_noise import snoise
from random_interpolator import RandomInterpolator
from state import State

from background import bgcolorInterpolator, bgtailInterpolator


seed_list = [
    66359,  23802,  72212,  87422,  93711,  60901, 102507,  86383,
    85871,  29174,  67382,  31268,  49904,  46217,  36448,   4085,
    83402, 100324,  38140,  45713,  43896,  16853,  86778,   3440,
    76750,  14508,  19974,  87937,  25580,  49236,  14495,  41940,
    69652,  15417,  50981,  73977,  74383,  48582,  54104,  45674,
    99805,   3940,  14555,  59095,  44172,  42904,  50004,  68999,
    9507,  87843, 100043,  88797,  74890,  60940,  53515,  51485,
    10603,  57034,  89593,  54704,  50310,  70297,  36594,  41455,
    71175,  16918,  18941,  16480,  69407,  98259,  66323,  60134,
    55220,  74973,  40513,  68977,  58235,  51438,  10734,  22637,
    19618,  78404,  52584,  33885,  88093,  43323,  49493,  95712,
    96190,  27274,  95760,  15794,  11261,  16946,  12098,  48366,
    100148,  14988,  76259,  53729,
]

seedInterpolator = RandomInterpolator(
    30,
    seed_list,
    0,
)

freqInterpolator = RandomInterpolator(
    200,
    [1/200, 1/100, 1/500, 1/10],
    0.3,
)

rng = np.random.default_rng()


def curl_func(coords, add_freq=0):
    res = 1 * snoise(
        coords,
        octaves=4,
        frequency=freqInterpolator.get()+add_freq,
        seed=int(seedInterpolator.get()),
    )
    return res


def grad(y, h=1e-2, add_freq=0):
    ret = np.zeros((2, y.shape[1]))
    vec = np.zeros((3, y.shape[1]))
    vec[:2] = y

    for it in range(2):
        dir = np.zeros(3)
        dir[it] = 1.

        pfield = curl_func((vec + dir[:, None] * h), add_freq=add_freq)
        nfield = curl_func((vec - dir[:, None] * h), add_freq=add_freq)
        ret[it] = ((pfield - nfield) / (2 * h))

    curl = np.array(
        [
            ret[1],
            -ret[0],
        ],
    )
    return curl


class Shadows2(State):
    def __init__(self, n=10):
        self.sprite_list = arcade.SpriteList()
        self.sprite_shadow = arcade.Sprite("./visual_assets/shadow.png")
        self.sprite_hill = arcade.Sprite("./visual_assets/hill.png")

        self.sprite_test = arcade.SpriteCircle(50, arcade.color.WHITE, True)

        self.shapes = arcade.ShapeElementList()
        self.sprite_list.append(self.sprite_test)

        self.sprite_list.append(self.sprite_shadow)
        self.sprite_list.append(self.sprite_hill)

        self.n = n

        self.background_intensity = 0

        self.rms_limited = 0.0
        self.rms = 0.0

        self.coords = rng.uniform(size=(2, self.n))
        self.colors = rng.integers(low=0, high=255, size=(3, self.n))

        self.add_freq = 0

        #self.old_shape = arcade.create_ellipse(0.0, 0.0, 1, 1, arcade.color.WHITE)


        self.color1 = (200 * self.background_intensity, 137 * self.background_intensity, 133 * self.background_intensity, 0)

        self.shape = arcade.create_ellipse(0.0, 0.0, 300, 300, self.color1)

        self.shape_height = 0

        self.update(0, 0)

    def get_coords(self, width, height):
        return (
            self.coords * np.array([width, height])[:, None]
            % np.array([width, height])[:, None]
        )

    def update_window(self, width, height, **kwargs):
        pass

    def update(self, elapsed_time, delta_time, **kwargs):
        if 'rms_buffer' in kwargs:
            rms_buffer = kwargs.get('rms_buffer')
            self.background_intensity = np.clip(
                10 * (
                    (np.max(rms_buffer[:3]) - np.mean(rms_buffer[:3]))
                    / (np.max(rms_buffer) + 1e-10)
                ),
                None,
                1,
            )
        if 'kick' in kwargs:
            kick = kwargs.get('kick')
            if kick:
                self.add_freq += 0.05
        
        if 'rms_limited' in kwargs:
            self.rms_limited = kwargs.get('rms_limited')
        
        if 'rms' in kwargs:
            self.rms = 100 * kwargs.get('rms')

        seedInterpolator.update(delta_time)
        freqInterpolator.update(delta_time)
        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)

        width, height = arcade.get_window().get_size()
        self.coords += (
            grad(self.get_coords(width, height), add_freq=self.add_freq)
            * delta_time
        )

        self.add_freq = np.clip(self.add_freq - 0.005, 0., 0.8)

        self.color1 = (200 * int(self.background_intensity), 137 * int(self.background_intensity), 133 * int(self.background_intensity))

        self.shape_height = (height / 6) * int(self.rms)
        self.shape = arcade.create_ellipse_filled(width //2, 0, width, height / 2, self.color1)

        self.sprite_test.color = self.color1
        self.sprite_test.radians = self.shape_height
        self.sprite_list.update()



    def draw(self, width, height, **kwargs):
        bgcolor = bgcolorInterpolator.get()
        arcade.draw_rectangle_filled(
            width // 2,
            height // 2,
            width,
            height,
            color=(
                bgcolor[0] * (0.05 + 0.9 * self.background_intensity),
                bgcolor[1] * (0.05 + 0.9 * self.background_intensity),
                bgcolor[2] * (0.05 + 0.9 * self.background_intensity),
                255,
            ),
        )

        arcade.draw_points(
            self.get_coords(width=width, height=height).T,
            arcade.color.WHITE,
            2,
        )

        is_sun = (127 * int(self.background_intensity)) > 0.0
        if is_sun:
            color1 = (200 * int(self.background_intensity), 137 * int(self.background_intensity), 133 * int(self.background_intensity) , 127 * int(self.background_intensity))
        else:
            color1 = (0, 0, 0, 1)


        color2 = (7 * int(self.background_intensity), 67 * int(self.background_intensity), 88 * int(self.background_intensity), int(self.background_intensity))
        
        #arcade.draw_line(0.0, 0.0 + 100 * self.rms, width // 2, height // 2, arcade.color.WHITE, 1)


        # self.old_shape = self.shape

        
        # self.shapes.remove(self.old_shape)
        # self.shapes.dirties.clear()

        # self.shapes = arcade.ShapeElementList()

        self.shape.draw()

        self.sprite_test.center_x = width / 2
        self.sprite_test.center_y = height / 2

        self.sprite_shadow.scale = width/9/width 
        self.sprite_shadow.center_x = width / 2
        self.sprite_shadow.center_y = height / 3

        self.sprite_hill.width = width
        self.sprite_hill.height = width*1080/1920
        self.sprite_hill.center_x = width / 2
        self.sprite_hill.center_y = self.sprite_hill.height / 2

        self.sprite_list.draw()

        
