from random import Random

from .constants import RANDOM_SEED

def random():
    return Random(RANDOM_SEED)