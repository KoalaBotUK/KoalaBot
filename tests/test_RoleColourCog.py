#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import mock
import pytest
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import RoleColourCog

# Constants

# Variables
role_colour_cog = None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global role_colour_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    role_colour_cog = RoleColourCog.RoleColourCog(bot)
    bot.add_cog(role_colour_cog)
    dpytest.configure(bot)
    print("Tests starting")
