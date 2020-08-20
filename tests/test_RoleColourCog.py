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
from cogs import ColourRole

# Constants

# Variables
role_colour_cog = None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global role_colour_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    role_colour_cog = ColourRole.ColourRole(bot)
    bot.add_cog(role_colour_cog)
    dpytest.configure(bot)
    print("Tests starting")


@pytest.mark.asyncio
async def test_colour_change_perm_check_valid():
    assert False


@pytest.mark.asyncio
async def test_colour_change_perm_check_invalid():
    assert False


@pytest.mark.asyncio
async def test_command_missing_args():
    assert False


@pytest.mark.asyncio
async def test_command_valid_args():
    assert False


@pytest.mark.asyncio
async def test_command_invalid_args():
    assert False


@pytest.mark.asyncio
async def test_colour_check_valid_colour():
    assert False


@pytest.mark.asyncio
async def test_colour_check_invalid_colour():
    assert False

