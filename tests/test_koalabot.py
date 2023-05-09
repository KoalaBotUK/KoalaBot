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
import pytest_asyncio
from discord.ext import commands

# Own modules
import koalabot
from koala.db import clear_all_tables, fetch_all_tables
from tests.tests_utils.last_ctx_cog import LastCtxCog
from tests.tests_utils.utils import FakeAuthor

# Constants

# Variables
utils_cog = None


@pytest_asyncio.fixture(autouse=True)
async def test_ctx(bot: commands.Bot):
    global utils_cog
    utils_cog = LastCtxCog(bot)
    await bot.add_cog(utils_cog)
    dpytest.configure(bot)
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    return utils_cog.get_last_ctx()


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    clear_all_tables(fetch_all_tables())


@pytest_asyncio.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest


def test_test_user_is_owner(test_ctx):
    assert koalabot.is_owner_ctx(test_ctx)


def test_invalid_test_user_is_owner(test_ctx):
    for i in range(len(koalabot.BOT_OWNER)):
        test_ctx.author = FakeAuthor(id=koalabot.BOT_OWNER[i] + 1)
        koalabot.is_dpytest = False
        assert not koalabot.is_owner_ctx(test_ctx)
        koalabot.is_dpytest = True


def test_owner_is_owner(test_ctx):
    for i in range(len(koalabot.BOT_OWNER)):
        test_ctx.author = FakeAuthor(id=koalabot.BOT_OWNER[i])
        assert koalabot.is_owner_ctx(test_ctx)


def test_test_user_is_admin(test_ctx):
    assert koalabot.is_admin(test_ctx)


def test_invalid_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(id=int(koalabot.BOT_OWNER[0]) + 2)
    koalabot.is_dpytest = False
    assert not koalabot.is_admin(test_ctx)
    koalabot.is_dpytest = True


def test_admin_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0001", all_permissions=True)
    assert koalabot.is_admin(test_ctx)


def test_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002", all_permissions=True)
    assert koalabot.is_admin(test_ctx)


def test_not_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(all_permissions=False)
    koalabot.is_dpytest = False
    assert not koalabot.is_admin(test_ctx)
    koalabot.is_dpytest = True


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@mock.patch("koalabot.ENABLED_COGS", ['greetings_cog'])
@pytest.mark.asyncio
async def test_load_all_cogs(bot):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await koalabot.load_all_cogs(bot)
    mock1.assert_called_with(".greetings_cog", package="tests.tests_utils.fake_load_all_cogs")




@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    koalabot.is_dpytest = True
    yield
    koalabot.is_dpytest = False
