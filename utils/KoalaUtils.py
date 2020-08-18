#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random

# Libs

# Own modules

# Constants
ID_LENGTH = 18

# Variables


def random_id():
    range_start = 10**(ID_LENGTH-1)
    range_end = (10**ID_LENGTH)-1
    return random.randint(range_start, range_end)
