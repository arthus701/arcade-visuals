import arcade


class State(object):
    def __init__(self, *args, **kwargs):
        pass

    def update(self, elapsed_time, delta_time):
        pass

    def draw(self, elapsed_time, delta_time):
        pass


class InitialState(State):
    def draw(self, elapsed_time, delta_time):
        width, height = arcade.get_window().get_size()
        arcade.draw_text(
            "Select state using the number keys.\n"
            "1: Sun\n"
            "2: Point cloud",
            0,
            2*height//3,
            width=width,
            align="center"
        )
