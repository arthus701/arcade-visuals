import numpy as np
import arcade
from simplex_noise import snoise
from random_interpolator import RandomInterpolator
from state import State
from background import bgcolorInterpolator, bgtailInterpolator
from parameters import ang_reso
from audio_client import AudioParameters
from Counter import Counter
from sun import Sun


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

random_shadows = [
    "tree",
    "hill",
    "butterfly",
    "flowers"
]


class Shadows(State):

    center_variations = [
        "girl",
    ]

    center_duration = 60 * 10

    def __init__(self, n=10):
        self.sun = Sun(0)

        ## Setup Sprites
        self.sprites_list = arcade.SpriteList()
        self.sprite_girl = arcade.Sprite("./visual_assets/girl.png")
        self.sprite_tree = arcade.Sprite("./visual_assets/tree.png")
        self.sprite_hill = arcade.Sprite("./visual_assets/hill.png")
        self.sprite_butterfly = arcade.Sprite("./visual_assets/butterfly.png")
        self.sprite_flowers = arcade.Sprite("./visual_assets/flowers.png")
        self.sprite_birds_l = arcade.Sprite("./visual_assets/birds_l.png")
        self.sprite_birds_r = arcade.Sprite("./visual_assets/birds_r.png")

        self.sprites_list.append(self.sprite_girl)
        self.sprites_list.append(self.sprite_tree)
        self.sprites_list.append(self.sprite_hill)
        self.sprites_list.append(self.sprite_butterfly)
        self.sprites_list.append(self.sprite_flowers)
        self.sprites_list.append(self.sprite_birds_l)
        self.sprites_list.append(self.sprite_birds_r)

        self.sprite_options = {
            "girl": {
                "show": True,
                "pop": False
            },
            "tree": {
                "show": False,
                "pop": False
            },
            "hill": {
                "show": False,
                "pop": False
            },
            "butterfly": {
                "show": False,
                "pop": False
            },
            "flowers": {
                "show": False,
                "pop": False
            },
            "birds_l": {
                "show": False,
                "pop": False
            },
            "birds_r": {
                "show": False,
                "pop": False
            },
        }

        self.show_sun = False

        self.current_center_idx = 0
        self.current_shadow_idx = 0

        self.center_counter = 0.0
        self.pop_counter = 0.0
        self.birds_counter = 0.0
        self.random_shadow_counter = 0.0
        self.angs_shape_counter = 0.0
        self.sun_counter = 0.0

        self.bgtail = 10

        ## Setup lines
        self.shape = np.zeros((2, ang_reso))
        self.left_line = np.zeros((2, ang_reso))
        self.right_line = np.zeros((2, ang_reso))

        self.n = n

        self.background_intensity = 1
        self.freq = 1/3000

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

    def update(self, elapsed_time, delta_time, audio_parameters: AudioParameters, **kwargs):
        width, height = arcade.get_window().get_size()

        bgcolorInterpolator.update(delta_time)
        bgtailInterpolator.update(delta_time)

        self.center_counter += delta_time
        self.pop_counter += delta_time
        self.birds_counter += delta_time
        self.random_shadow_counter += delta_time
        self.sun_counter += delta_time
        self.angs_shape_counter += 0.1

        self.params = audio_parameters

        high_and_mid = (self.params.high_rms_limited_value + self.params.mid_rms_limited_value) / 2
        if high_and_mid == 0:
            if self.params.rms_limit_threshold == 0:
                self.bgtail = 10
            else:
                t = (high_and_mid * 10 / self.params.rms_limit_threshold * 10)
                self.bgtail = min((250 * t) + 10, 50)
        else:
            self.bgtail = 150
        


        if 'rms' in kwargs:
            self.rms = kwargs.get('rms')
        
        if self.sun_counter >= 60.0 and self.show_sun:
            self.show_sun = False
            self.sun_counter = 0.0
        
        if self.sun_counter >= 60.0 * 9 and self.show_sun:
            self.show_sun = True
            self.sun_counter = 0.0
        

        self.background_intensity = 10 * self.params.rms_value
        
        
        if self.center_counter >= 60:
            self.sprite_options[self.center_variations[self.current_center_idx]]["show"] = False

            self.current_center_idx += 1
            if self.current_center_idx == len(self.center_variations):
                self.current_center_idx = 0

            self.sprite_options[self.center_variations[self.current_center_idx]]["show"] = True
            self.center_counter = 0.0

        if self.params.kick and self.pop_counter >= 5.0:
           self.sprite_options[self.center_variations[self.current_center_idx]]["pop"] = True
           self.pop_counter = 0.0
        
        if self.birds_counter >= 15.0:
            self.sprite_options["birds_l"]["show"] = True
                  
        self.sprite_options["birds_l"]["show"] = 15.0 <= self.birds_counter <= 15.05
        self.sprite_options["birds_r"]["show"] = 15.10 <= self.birds_counter <= 15.15
        if self.birds_counter >= 15.15:
            self.birds_counter = 0.0
        
        if self.random_shadow_counter >= 30.0 and self.random_shadow_counter < 30.05 \
            and self.sprite_options[self.center_variations[self.current_center_idx]]["show"] == True:
            self.current_shadow_idx = np.random.random_integers(0, 3)
            shadow = random_shadows[self.current_shadow_idx]
            if self.center_variations[self.current_center_idx] != shadow:
                self.sprite_options[shadow]["show"] = True
                self.sprite_options[self.center_variations[self.current_center_idx]]["show"] = False

        if self.random_shadow_counter >= 30.05:
            shadow = random_shadows[self.current_shadow_idx]
            self.sprite_options[shadow]["show"] = False
            self.sprite_options[self.center_variations[self.current_center_idx]]["show"] = True
            self.random_shadow_counter = 0.0

        arg = np.round(elapsed_time, 2)
        ang = self.rms / 20 * np.ones(self.left_line.shape[1])
        rotmat = np.array(
            [
                [np.cos(ang), np.sin(ang)],
                [-np.sin(ang), np.cos(ang)],
            ]
        )


        ang_shape = self.params.mid_rms_value / 20 * np.ones(self.shape.shape[1])
        rotmat_shape = np.array(
            [
                [np.cos(ang_shape), np.sin(ang_shape)],
                [-np.sin(ang_shape), np.cos(ang_shape)],
            ]
        )
        shape_f = self.params.high_rms_limited_value
        if shape_f == 0:
            shape_f = 0.0001
        rad_shape_add = self.rms * 400 + self.rms * 100
        rad_right = self.rms * 400 + self.rms * 100
        rad_left = self.rms * 4 + self.rms * 10
        rad = np.array(
            [
                np.ones(ang_reso),
                1 * func(elapsed_time, self.left_line, freq=self.freq),
            ]
        )

        rad_shape = np.array(
            [
                np.ones(ang_reso),
                1 * func(delta_time, self.shape, freq=1/8000),
            ]
        )

        offset = np.array(
            [
                width // 2,
                height // 2,
            ]
        )

        scale = min(width, height) / max(self.params.high_rms_limited_value, 1)
        scale_shape = min(width, height) / 5

        angs = np.linspace(0, 180, ang_reso)

        if self.angs_shape_counter > 360:
            self.angs_shape_counter = 0.0
        angs_shape = np.linspace(0, min(self.params.mid_rms_value * 360, 360), ang_reso)


        shape = np.einsum(
            'ijk, jk->ik',
            scale_shape * rotmat,
            rad_shape,
        ) * np.array(
            [
                -np.sin(np.deg2rad(angs_shape)),
                -np.cos(np.deg2rad(angs_shape)),
                
            ]
        )

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

        self.shape = (1 + rad_shape_add) * shape + offset[:, None]

        self.left_line = (1 + rad_left) * line + offset[:, None]
        self.right_line = (1 - rad_right) * line2 + offset[:, None]

        if self.show_sun:
            self.sun.update(elapsed_time, delta_time, audio_parameters, **kwargs)
            self.sun.glow_max = 0




    def draw(self, width, height, **kwargs):
        
        bgcolor = bgcolorInterpolator.get()
        if self.show_sun:
            self.sun.draw(width, height, background_intensity=self.background_intensity, bgcolor=bgcolor, bgtail=min(bgtailInterpolator.get() * self.params.high_rms_value * 100, 255))
        else:
            arcade.draw_rectangle_filled(
                width // 2,
                height // 2,
                width,
                height,
                color=(
                    bgcolor[0] * (0.1 + 0.9 * self.background_intensity),
                    bgcolor[1] * (0.1 + 0.9 * self.background_intensity),
                    bgcolor[2] * (0.1 + 0.9 * self.background_intensity),
                    self.bgtail,
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

        arcade.draw_line_strip(
            self.shape.T,
            arcade.color.SHADOW,
            1
        )

        self.sprite_girl.scale = width/7/width
        self.sprite_girl.center_x = width / 2
        self.sprite_girl.center_y = height / 2

        self.sprite_tree.scale = width/width
        self.sprite_tree.center_x = width / 2
        self.sprite_tree.center_y = height / 2

        self.sprite_hill.scale = width/width
        self.sprite_hill.center_x = width / 2
        self.sprite_hill.center_y = height / 2

        self.sprite_butterfly.scale = width/4/width
        self.sprite_butterfly.center_x = width / 2
        self.sprite_butterfly.center_y = height / 2
        
        self.sprite_flowers.scale = width/width
        self.sprite_flowers.center_x = width / 2
        self.sprite_flowers.center_y = height / 2
        
        self.sprite_birds_l.scale = width/2/width
        self.sprite_birds_l.center_x = width / 4
        self.sprite_birds_l.center_y = height / 2

        self.sprite_birds_r.scale = width/2/width
        self.sprite_birds_r.center_x = (width / 2) + (width / 4)
        self.sprite_birds_r.center_y = height / 2

        if not self.sprite_options["girl"]["show"]:
            self.sprite_girl.scale = 0
        if not self.sprite_options["tree"]["show"]:
            self.sprite_tree.scale = 0
        if not self.sprite_options["hill"]["show"]:
            self.sprite_hill.scale = 0
        if not self.sprite_options["butterfly"]["show"]:
            self.sprite_butterfly.scale = 0
        if not self.sprite_options["flowers"]["show"]:
            self.sprite_flowers.scale = 0
        if not self.sprite_options["birds_l"]["show"]:
            self.sprite_birds_l.scale = 0
        if not self.sprite_options["birds_r"]["show"]:
            self.sprite_birds_r.scale = 0
        
        if self.sprite_options["girl"]["pop"]:
            self.sprite_girl.scale *= 1.5
            self.sprite_options["girl"]["pop"] = False
        if self.sprite_options["tree"]["pop"]:
            self.sprite_tree.scale *= 1.5
            self.sprite_options["tree"]["pop"] = False
        if self.sprite_options["hill"]["pop"]:
            self.sprite_hill.scale *= 1.5
            self.sprite_options["hill"]["pop"] = False
        if self.sprite_options["butterfly"]["pop"]:
            self.sprite_butterfly.scale *= 1.5
            self.sprite_options["butterfly"]["pop"] = False
        if self.sprite_options["flowers"]["pop"]:
            self.sprite_flowers.scale *= 1.5
            self.sprite_options["flowers"]["pop"] = False
        if self.sprite_options["birds_l"]["pop"]:
            self.sprite_birds_l.scale *= 1.5
            self.sprite_options["birds_l"]["pop"] = False
        if self.sprite_options["birds_r"]["pop"]:
            self.sprite_birds_r.scale *= 1.5
            self.sprite_options["birds_r"]["pop"] = False


        self.sprites_list.draw()
        # self.sprite_birds_l.draw()
        # self.sprite_birds_r.draw()
        # self.sprite_tree.draw()
        # self.sprite_hill.draw()
        # self.sprite_butterfly.draw()
        # self.sprite_flowers.draw()
        # self.sprite_girl.draw()

        
