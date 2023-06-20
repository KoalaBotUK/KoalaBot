#!/usr/bin/env python

"""
Testing KoalaBot Utils

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
from koala.utils import __parse_args, format_config_path, wait_for_message
from tests.log import logger
from tests.tests_utils.last_ctx_cog import LastCtxCog


# Constants

# Variables


def test_parse_args_config():
    assert "/config/" == vars(__parse_args(["--config", "/config/"])).get("config")


def test_parse_args_invalid():
    assert vars(__parse_args(["--test", "/test/"])).get("config") is None


@mock.patch("os.name", "posix")
def test_format_db_path_linux_absolute():
    db_path = format_config_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/test.db"


@mock.patch("os.name", "nt")
def test_format_db_path_windows():
    db_path = format_config_path("/test_dir/", "windows_test.db")
    assert db_path == "\\test_dir\\windows_test.db"


@pytest.mark.parametrize("msg_content", [" ", "something"])
@pytest.mark.asyncio
async def test_wait_for_message_not_none(msg_content, utils_cog: LastCtxCog):
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    bot: discord.Client = config.client
    import threading
    t2 = threading.Timer(interval=0.1, function=dpytest.message, args=(msg_content))
    t2.start()
    fut = await wait_for_message(bot, ctx, 0.2)
    t2.join()
    assert fut, dpytest.sent_queue


@pytest.mark.asyncio
async def test_wait_for_message_none(utils_cog: LastCtxCog):
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    bot: discord.Client = config.client
    msg, channel = await wait_for_message(bot, ctx, 0.2)
    assert not msg
    assert channel == ctx.channel


@pytest_asyncio.fixture(autouse=True)
async def utils_cog(bot: commands.Bot):
    utils_cog = LastCtxCog(bot)
    await bot.add_cog(utils_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return utils_cog