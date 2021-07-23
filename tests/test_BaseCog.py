#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

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
from cogs import BaseCog
from tests.utils_testing.TestUtils import assert_activity


# Constants

# Variables


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False
    KoalaBot


# Test TwitchAlert
@pytest.fixture(scope='function', autouse=True)
async def base_cog(bot):
    """ setup any state specific to the execution of the given module."""
    base_cog = BaseCog.BaseCog(bot)
    bot.add_cog(base_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return base_cog


@pytest.mark.asyncio
async def test_on_ready(base_cog: BaseCog.BaseCog):
    await base_cog.on_ready()
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.playing,
                                             name=KoalaBot.COMMAND_PREFIX + "help" + KoalaBot.KOALA_PLUG))


@pytest.mark.asyncio
async def test_change_activity():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "change_activity watching you")
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.watching, name="you" + KoalaBot.KOALA_PLUG))
    assert dpytest.verify().message().content("I am now watching you")


@pytest.mark.asyncio
async def test_invalid_change_activity():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "change_activity oof you")
    assert dpytest.verify().message().content("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")


def test_playing_new_discord_activity():
    test_name = "Half Life 3"
    assert_activity(BaseCog.new_discord_activity("playing", test_name),
                    type=discord.ActivityType.playing, name=test_name + KoalaBot.KOALA_PLUG)


def test_watching_new_discord_activity():
    test_name = "you"
    assert_activity(BaseCog.new_discord_activity("watching", test_name),
                    type=discord.ActivityType.watching, name=test_name + KoalaBot.KOALA_PLUG)


def test_listening_new_discord_activity():
    test_name = "/Darude Sandstorm"
    assert_activity(BaseCog.new_discord_activity("listening", test_name),
                    type=discord.ActivityType.listening, name=test_name + KoalaBot.KOALA_PLUG)


def test_streaming_new_discord_activity():
    test_name = "__your room__"
    assert_activity(BaseCog.new_discord_activity("streaming", test_name),
                    type=discord.ActivityType.streaming, name=test_name + KoalaBot.KOALA_PLUG,
                    url=KoalaBot.STREAMING_URL)


def test_custom_new_discord_activity():
    test_name = "1 4M K04L4"
    assert_activity(BaseCog.new_discord_activity("custom", test_name),
                    type=discord.ActivityType.custom, name=test_name + KoalaBot.KOALA_PLUG)


def test_invalid_new_discord_activity():
    test_name = "INCORRECT"
    with pytest.raises(SyntaxError, match="incorrect is not an activity"):
        BaseCog.new_discord_activity("incorrect", test_name)


@mock.patch("builtins.round", mock.MagicMock(return_value=4))
@pytest.mark.asyncio
async def test_ping(base_cog: BaseCog.BaseCog):
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ping")
    assert dpytest.verify().message().content("Pong! 4ms")


@pytest.mark.asyncio
async def test_support():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "support")
    assert dpytest.verify().message().content("Join our support server for more help! https://discord.gg/5etEjVd")


@pytest.mark.asyncio
async def test_default_clear():
    with mock.patch.object(discord.TextChannel, 'purge') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "clear")
    mock1.assert_called_with(limit=2)


@pytest.mark.asyncio
async def test_clear():
    with mock.patch.object(discord.TextChannel, 'purge') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "clear 4")
    mock1.assert_called_with(limit=5)


@pytest.mark.asyncio
async def test_invalid_clear(base_cog: BaseCog.BaseCog):
    with pytest.raises(discord.ext.commands.errors.BadArgument,
                       match="Converting to \"int\" failed for parameter \"amount\"."):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "clear a")


@pytest.mark.asyncio
async def test_load_cog(base_cog: BaseCog.BaseCog):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "load_cog BaseCog")
    mock1.assert_called_with('cogs.BaseCog')


@pytest.mark.asyncio
async def test_invalid_load_cog(base_cog: BaseCog.BaseCog):
    with pytest.raises(discord.ext.commands.errors.CommandInvokeError,
                       match=r".* Extension 'cogs.FakeCog' could not be loaded."):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "load_cog FakeCog")


@pytest.mark.asyncio
async def test_unload_base_cog(base_cog: BaseCog.BaseCog):
    with mock.patch.object(discord.ext.commands.Context, 'send') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unload_cog BaseCog")
    mock1.assert_called_with("Sorry, you can't unload the base cog")


@pytest.mark.asyncio
async def test_load_valid_cog(base_cog: BaseCog.BaseCog):
    base_cog.COGS_DIR = "tests/fake_load_all_cogs"
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "load_cog Greetings")
    mock1.assert_called_with("tests.fake_load_all_cogs.Greetings")


@pytest.mark.asyncio
async def test_load_and_unload_valid_cog(base_cog: BaseCog.BaseCog):
    base_cog.COGS_DIR = "tests/fake_load_all_cogs"
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "load_cog Greetings")
    mock1.assert_called_with("tests.fake_load_all_cogs.Greetings")

    with mock.patch.object(discord.ext.commands.bot.Bot, 'unload_extension') as mock1:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unload_cog Greetings")
    mock1.assert_called_with('tests.fake_load_all_cogs.Greetings')


@pytest.mark.asyncio
async def test_invalid_unload_cog(base_cog: BaseCog.BaseCog):
    with pytest.raises(discord.ext.commands.errors.CommandInvokeError,
                       match="Command raised an exception: ExtensionNotLoaded:"
                             " Extension 'cogs.FakeCog' has not been loaded."):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unload_cog FakeCog")


@pytest.mark.asyncio
async def test_setup():
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        BaseCog.setup(KoalaBot.client)
    mock1.assert_called()
