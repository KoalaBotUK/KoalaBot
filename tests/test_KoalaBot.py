#!/usr/bin/env python

"""
Koala Bot Base Code

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
import discord
from discord.ext import commands, tasks
import discord.ext.test as dpytest
import mock
import pytest
from dotenv import load_dotenv

# Own modules
import KoalaBot
from tests.utils.TestUtilsCog import TestUtilsCog
from tests.utils.TestUtils import FakeAuthor


# Constants
load_dotenv()
BOT_NAME = os.environ['DISCORD_NAME']
BOT_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
BOT_TOKEN = os.environ['DISCORD_TOKEN']

# Variables

utils_cog = None


@pytest.fixture
async def test_ctx():
    """ setup any state specific to the execution of the given module."""
    global utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    utils_cog = TestUtilsCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    # print("Tests starting")
    return utils_cog.get_last_ctx()


def test_testuser_is_owner(test_ctx):
    assert KoalaBot.is_owner(test_ctx)


def test_invalid_testuser_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002")
    assert not KoalaBot.is_owner(test_ctx)


def test_owner_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(id=KoalaBot.BOT_OWNER)
    assert KoalaBot.is_owner(test_ctx)


def test_testuser_is_admin(test_ctx):
    assert KoalaBot.is_admin(test_ctx)


def test_invalid_testuser_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002")
    assert not KoalaBot.is_admin(test_ctx)


def test_admin_testuser_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0001", allPermissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002", allPermissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_not_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(allPermissions=False)
    assert not KoalaBot.is_admin(test_ctx)


def test_load_all_cogs():
    test_koala = KoalaBot
    test_koala.COGS_DIR = "tests/fake_load_all_cogs"
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        test_koala.load_all_cogs()
    mock1.assert_called_with("tests.fake_load_all_cogs.Greetings")

