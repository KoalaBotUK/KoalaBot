#!/usr/bin/env python

"""
Testing KoalaBot Base Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import argparse

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from tests.utils_testing.TestUtils import FakeAuthor
from tests.utils_testing.LastCtxCog import LastCtxCog
from utils.KoalaDBManager import KoalaDBManager

# Constants

# Variables
utils_cog = None
DBManager = KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY, KoalaBot.config_dir)
DBManager.create_base_tables()


@pytest.fixture(autouse=True)
async def test_ctx(bot):
    global utils_cog
    utils_cog = LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    return utils_cog.get_last_ctx()


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.clear_all_tables(DBManager.fetch_all_tables())
    yield DBManager


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest


def test_parse_args_config():
    assert "/config/" == vars(KoalaBot.parse_args(["--config", "/config/"])).get("config")


def test_parse_args_invalid():
    with mock.patch.object(argparse.ArgumentParser, 'exit') as mock1:
            KoalaBot.parse_args(["--test", "/test/"])
    mock1.assert_called_once()


def test_test_user_is_owner(test_ctx):
    assert KoalaBot.is_owner(test_ctx)


def test_invalid_test_user_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(id=int(KoalaBot.BOT_OWNER)+1)
    KoalaBot.is_dpytest = False
    assert not KoalaBot.is_owner(test_ctx)
    KoalaBot.is_dpytest = True


def test_owner_is_owner(test_ctx):
    test_ctx.author = FakeAuthor(id=int(KoalaBot.BOT_OWNER))
    assert KoalaBot.is_owner(test_ctx)


def test_test_user_is_admin(test_ctx):
    assert KoalaBot.is_admin(test_ctx)


def test_invalid_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(id=int(KoalaBot.BOT_OWNER)+2)
    KoalaBot.is_dpytest = False
    assert not KoalaBot.is_admin(test_ctx)
    KoalaBot.is_dpytest = True


def test_admin_test_user_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0001", all_permissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(name="TestUser#0002", all_permissions=True)
    assert KoalaBot.is_admin(test_ctx)


def test_not_admin_is_admin(test_ctx):
    test_ctx.author = FakeAuthor(all_permissions=False)
    KoalaBot.is_dpytest = False
    assert not KoalaBot.is_admin(test_ctx)
    KoalaBot.is_dpytest = True


def test_load_all_cogs():
    test_koala = KoalaBot
    test_koala.COGS_DIR = "tests/fake_load_all_cogs"
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        test_koala.load_all_cogs()
    mock1.assert_called_with("tests.fake_load_all_cogs.Greetings")


@pytest.mark.asyncio
async def test_dm_single_group_message():
    test_message = 'default message'
    test_member = dpytest.get_config().members[0]
    x = await KoalaBot.dm_group_message([test_member], test_message)
    assert dpytest.verify().message().content(test_message)
    assert x == 1


@pytest.mark.asyncio
async def test_dm_plural_group_message():
    test_message = 'default message'
    test_member = dpytest.get_config().members[0]
    test_member_2 = await dpytest.member_join()
    await dpytest.empty_queue()
    x = await KoalaBot.dm_group_message([test_member, test_member_2], test_message)
    assert dpytest.verify().message().content(test_message)
    assert dpytest.verify().message().content(test_message)
    assert x == 2


@pytest.mark.asyncio
async def test_dm_empty_group_message():
    test_message = 'this should not be sent'
    x = await KoalaBot.dm_group_message([], test_message)
    assert dpytest.verify().message().nothing()
    assert x == 0


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False
