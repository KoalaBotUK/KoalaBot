#!/usr/bin/env python

"""
Testing KoalaBot Base Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from tests.utils.TestUtils import FakeAuthor
from tests.utils.TestUtilsCog import TestUtilsCog

# Constants

# Variables
utils_cog = None


@pytest.fixture
async def test_ctx():
    global utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    utils_cog = TestUtilsCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    return utils_cog.get_last_ctx()


def test_test_user_is_owner(test_ctx):
    assert KoalaBot.is_owner(test_ctx)


def test_invalid_test_user_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002")
    assert not KoalaBot.is_owner(test_ctx)


def test_owner_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(id=int(KoalaBot.BOT_OWNER))
    assert KoalaBot.is_owner(test_ctx)


def test_test_user_is_admin(test_ctx):
    assert KoalaBot.is_admin(test_ctx)


def test_invalid_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002")
    assert not KoalaBot.is_admin(test_ctx)


def test_admin_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0001", all_permissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002", all_permissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_not_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(all_permissions=False)
    assert not KoalaBot.is_admin(test_ctx)


def test_load_all_cogs():
    test_koala = KoalaBot
    test_koala.COGS_DIR = "tests/fake_load_all_cogs"
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        test_koala.load_all_cogs()
    mock1.assert_called_with("tests.fake_load_all_cogs.Greetings")
