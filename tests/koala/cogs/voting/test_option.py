#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs

# Own modules
from koala.cogs.voting.option import Option


def test_option():
    opt = Option("test", "option", 123456789)
    assert opt.id == 123456789
    assert opt.head == "test"
    assert opt.body == "option"
