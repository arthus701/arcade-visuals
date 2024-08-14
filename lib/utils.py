import numpy as np
from simplex_noise import snoise


def func(coords, now, frequency, seed=141):
    _coords = np.vstack(
        (
            coords,
            now * np.ones((1, coords.shape[1])) * 100,
        ),
    )

    res = snoise(
        _coords,
        octaves=6,
        frequency=frequency,
        seed=seed,
    )
    
    res /= np.max(np.abs(res))
    
    return (res + 1) / 2


def curl_func(coords, frequency, seed):
    return 1 * snoise(
        coords,
        octaves=4,
        frequency=frequency,
        seed=int(seed),
    )


def grad(y, frequency, seed, h=1e-2):
    ret = np.zeros((2, y.shape[1]))
    vec = np.zeros((3, y.shape[1]))
    vec[:2] = y

    for it in range(2):
        dir = np.zeros(3)
        dir[it] = 1.

        pfield = curl_func((vec + dir[:, None] * h), frequency, seed)
        nfield = curl_func((vec - dir[:, None] * h), frequency, seed)
        ret[it] = ((pfield - nfield) / (2 * h))

    curl = np.array(
        [
            ret[1],
            -ret[0],
        ],
    )

    return curl