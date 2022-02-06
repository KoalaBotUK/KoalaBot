#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest

# Own modules
from koala.cogs import IntroCog
from tests.tests_utils.LastCtxCog import LastCtxCog


@pytest.fixture(autouse=True)
def utils_cog(bot):
    utils_cog = LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return utils_cog


@pytest.fixture(autouse=True)
def intro_cog(bot):
    intro_cog = IntroCog(bot)
    bot.add_cog(intro_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return intro_cog