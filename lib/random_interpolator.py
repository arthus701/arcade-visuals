from copy import deepcopy

import numpy as np


class RandomInterpolator(object):
    def __init__(
        self,
        span,
        statelist,
        exp=1,
        seed=None,
    ):
        self.span = span

        self.time = 0

        self.statelist = statelist
        self.new_value = statelist[0]
        self.old_value = deepcopy(self.new_value)

        self.exp = exp
        self.rng = np.random.default_rng(seed=seed)

    def get(self):
        return (
            (1 - self.time**self.exp) * self.old_value
            + self.time**self.exp * self.new_value
        )

    def update(self, dt):
        self.time += dt / self.span
        if 1. < self.time:
            self.time -= 1
            self.old_value = deepcopy(self.new_value)
            idx = self.rng.integers(len(self.statelist))
            # print(idx)
            self.new_value = self.statelist[idx]
