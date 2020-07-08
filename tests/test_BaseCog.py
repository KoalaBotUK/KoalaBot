#!/usr/bin/env python

"""
Koala Bot Base Cog Tests

Commented using reStructuredText (reST)
"""
__author__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures

# Built-in/Generic Imports
import os
import asyncio
import sys
from unittest import TestCase
import threading
import multiprocessing


# Libs
import discord.ext.test as dpytest
import pytest
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

# Own modules
import KoalaBot
from cogs import BaseCog, Greetings
from tests.utils.test_utils import assert_activity, run_bot, run_test_bot

# Constants
load_dotenv()
BOT_NAME = os.environ['DISCORD_NAME']
BOT_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
BOT_TOKEN = os.environ['DISCORD_TOKEN']

# Variables


def setup_function(function):
    """ setup any state specific to the execution of the given module."""
    global base_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    base_cog = BaseCog.BaseCog(bot)
    bot.add_cog(base_cog)
    dpytest.configure(bot)
    print("Tests starting")


@pytest.mark.asyncio
async def test_on_ready():
    await base_cog.on_ready()
    dpytest.verify_activity(discord.Activity(type=discord.ActivityType.playing,
                                             name=KoalaBot.COMMAND_PREFIX+"help"+KoalaBot.KOALA_PLUG))


@pytest.mark.asyncio
async def test_change_activity():
    await dpytest.message(KoalaBot.COMMAND_PREFIX+"change_activity watching you")
    dpytest.verify_activity(discord.Activity(type=discord.ActivityType.watching, name="you"+KoalaBot.KOALA_PLUG))
    dpytest.verify_message("I am now watching you")


def test_on_member_join():
    dpytest.member_join(user="Testies#0002")

    assert False


def test_on_member_remove():
    assert False


@pytest.mark.asyncio
async def test_ping():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ping")
    dpytest.verify_message("S")


def test_clear():
    assert False


def test_load_cog():
    assert False


def test_unload_cog():
    assert False