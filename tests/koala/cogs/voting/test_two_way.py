#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
# Libs

# Own modules
from koala.cogs.voting.two_way import TwoWay


def test_two_way():
    def test_asserts(f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except AssertionError:
            return
        raise AssertionError

    # test internal asserts don't false positive
    t = TwoWay({1: 2, 3: 4})
    t2 = TwoWay({1: 2, 2: 1, 4: 3})
    assert t == t2

    # test an invalid dict cannot be made
    test_asserts(TwoWay, {1: 2, 2: 3})

    def ta2():
        t = TwoWay()
        t[1] = 2
        t[2] = 3
        test_asserts(ta2)
