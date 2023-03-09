from random import Random
import time

from typing import Union

from .constants import RANDOM_SEED


def random(seed: Union[None, int, float, str, bytes, bytearray] = None) -> Random:
    """Returns a `Random` object using a specified seed."""
    return Random(seed or RANDOM_SEED)

def time_execution(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"{func}: {time.time() - start_time}")
        return result
    return wrapper