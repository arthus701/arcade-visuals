import numpy as np
import arcade
from simplex_noise import snoise
from random_interpolator import RandomInterpolator
from state import State
from background import bgcolorInterpolator, bgtailInterpolator
from parameters import ang_reso
from audio_client import AudioParameters


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


def func(now, coords, seed=141, freq=1/1200):
    _coords = np.vstack(
        (
            coords,
            now * np.ones((1, coords.shape[1])) * 100,
        ),
    )
    res = snoise(
        _coords,
        octaves=6,
        frequency=freq,
        seed=seed,
    )
    res /= np.max(np.abs(res))
    return (res + 1) / 2



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


class Shadows(State):
    def __init__(self, n=10):
        self.sprite_girl = arcade.Sprite("./visual_assets/girl.png")
        self.scale_girl = False

        self.sprite_tree = arcade.Sprite("./visual_assets/tree.png")
        self.show_tree = False

        self.sprite_birds_l = arcade.Sprite("./visual_assets/birds_l.png")
        self.show_birds_l = False

        self.sprite_birds_r = arcade.Sprite("./visual_assets/birds_r.png")
        self.show_birds_r = False

        self.left_line = np.zeros((2, ang_reso))
        self.right_line = np.zeros((2, ang_reso))

        self.n = n

        self.background_intensity = 1
        self.freq = 1/2400

        self.rms_limited = 0.0
        self.rms = 0.0
        self.kick = False
        self.last_kick = False
        self.count_1_sec = 0.0
        self.count_2_sec = 0.0
        self.count_3_sec = 0.0

        self.params = AudioParameters()

        self.update(0, 0, self.params)

    def update_window(self, width, height, **kwargs):
        pass

    def update(self, elapsed_time, delta_time, audio_parameters, **kwargs):

        self.count_1_sec += delta_time
        self.count_2_sec += delta_time
        self.count_3_sec += delta_time

        self.params = audio_parameters
        
        if 'kick' in kwargs:
            self.kick = kwargs.get('kick')
        
        if 'rms_limited' in kwargs:
            self.rms_limited = kwargs.get('rms_limited')
        
        if 'rms' in kwargs:
            self.rms = kwargs.get('rms')
        
        self.background_intensity = 1000 * self.rms_limited

        if self.kick:
            self.background_intensity = 100


        print(elapsed_time, delta_time)
        if self.kick and self.count_1_sec >= 5.0:
            self.scale_girl = True
            self.count_1_sec = 0.
        
        if self.count_2_sec >= 60.0:
            self.show_tree = True

        if self.count_2_sec >= 60.05:
            self.show_tree = False
            self.count_2_sec = 0.0

        if self.count_3_sec >= 15.0:
            self.show_birds_l = True
        
        if self.count_3_sec >= 15.05:
            self.show_birds_l = False
        
        if self.count_3_sec >= 15.10:
            self.show_birds_r = True
        
        if self.count_3_sec >= 15.15:
            self.show_birds_r = False
            self.count_3_sec = 0.0

        width, height = arcade.get_window().get_size()

        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)

        arg = np.round(elapsed_time, 2)
        ang = self.rms / 20 * np.ones(self.left_line.shape[1])
        rotmat = np.array(
            [
                [np.cos(ang), np.sin(ang)],
                [-np.sin(ang), np.cos(ang)],
            ]
        )

        rad_right = self.rms * 400 + self.rms * 100
        rad_left = self.rms * 4 + self.rms * 10
        rad = np.array(
            [
                np.ones(ang_reso),
                1 * func(elapsed_time, self.left_line, freq=self.freq),
            ]
        )

        offset = np.array(
            [
                width // 2,
                height // 2,
            ]
        )

        scale = min(width, height) / max(self.params.high_rms_limited_value, 1)

        angs = np.linspace(0, 180, ang_reso)
        line = np.einsum(
            'ijk, jk->ik',
            scale * rotmat,
            rad,
        ) * np.array(
            [
                -np.sin(np.deg2rad(angs)),
                -np.cos(np.deg2rad(angs)),
                
            ]
        )

        line2 = np.einsum(
            'ijk, jk->ik',
            scale * rotmat,
            rad,
        ) * np.array(
            [
                np.sin(np.deg2rad(angs)),
                np.cos(np.deg2rad(angs)),
            ]
        )

        self.left_line = (1 + rad_left) * line + offset[:, None]
        self.right_line = (1 - rad_right) * line2 + offset[:, None]




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

        arcade.draw_line_strip(
            self.left_line.T,
            arcade.color.WHITE,
            3
        )

        arcade.draw_line_strip(
            self.right_line.T,
            arcade.color.WHITE,
            3
        )

        self.sprite_girl.scale = width/7/width
        self.sprite_girl.center_x = width / 2
        self.sprite_girl.center_y = height / 2

        self.sprite_tree.scale = width/2/width
        self.sprite_tree.center_x = width / 2
        self.sprite_tree.center_y = height / 2

        self.sprite_birds_l.scale = width/2/width
        self.sprite_birds_l.center_x = width / 4
        self.sprite_birds_l.center_y = height / 2

        self.sprite_birds_r.scale = width/2/width
        self.sprite_birds_r.center_x = (width / 2) + (width / 4)
        self.sprite_birds_r.center_y = height / 2

        if self.scale_girl:
            self.scale_girl = False
            self.sprite_girl.scale *= 1.5
        
        if self.show_tree:
            self.sprite_girl.scale = 0
            

        if not self.show_tree:
            self.sprite_tree.scale = 0

        if not self.show_birds_l:
            self.sprite_birds_l.scale = 0
        
        if not self.show_birds_r:
            self.sprite_birds_r.scale = 0

        self.sprite_birds_l.draw()
        self.sprite_birds_r.draw()
        self.sprite_tree.draw()
        self.sprite_girl.draw()

        
