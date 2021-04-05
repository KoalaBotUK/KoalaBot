#!/usr/bin/env python

"""
Testing KoalaBot Insights Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import Insights
from tests.utils import TestUtilsCog

# Constants

# Variables
insights_cog: Insights.Insights = None
utils_cog: TestUtilsCog.TestUtilsCog = None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global insights_cog
    global utils_cog
    bot: commands.Bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    insights_cog = Insights.Insights(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(insights_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


@pytest.mark.asyncio
@pytest.mark.parametrize("num_guilds, num_users", [(1, 1), (1, 2), (1, 5), (2, 1), (2, 2), (5, 4), (5,10)])
async def test_insights(num_guilds, num_users):
    test_config = dpytest.get_config()
    client = test_config.client
    for i in range(num_guilds - 1):
        guild = dpytest.back.make_guild(f"Test Guild {i}")
        test_config.guilds.append(guild)

    for i in range(len(test_config.guilds)):
        for j in range(num_users - 1):
            await dpytest.member_join(i, client.user)
            await dpytest.member_join(i)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "insights")
    dpytest.verify_message(
        f"KoalaBot is in {len(dpytest.get_config().guilds)} servers with a member total of {2 * num_guilds * num_users}.")


@pytest.mark.asyncio
async def test_servers_no_args():
    test_config = dpytest.get_config()
    client = test_config.client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "servers")
    dpytest.verify_message("Test Guild 0")
    await dpytest.kick_callback(test_config.guilds[0], client.user)
    expected = ""
    for i in range(10):
        guild = dpytest.back.make_guild(f"Test Guild {i}")
        expected += f"Test Guild {i}, "
        test_config.guilds.append(guild)
        await dpytest.member_join(i, client.user)
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "servers", i)
        await dpytest.verify_message(expected[:-2])


@pytest.mark.asyncio
async def test_servers_fail_args():
    test_config = dpytest.get_config()
    client = test_config.client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "servers")
    dpytest.verify_message("Test Guild 0")
    await dpytest.kick_callback(test_config.guilds[0], client.user)
    arg = "fail_pls"
    for i in range(10):
        guild = dpytest.back.make_guild(f"Test Guild {i}")
        test_config.guilds.append(guild)
        await dpytest.member_join(i, client.user)
        await dpytest.message(KoalaBot.COMMAND_PREFIX + f"servers {arg}", i)
        await dpytest.verify_message(f"No servers with {arg} in their name")


@pytest.mark.asyncio
async def test_servers_with_args():
    test_config = dpytest.get_config()
    client = test_config.client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "servers")
    dpytest.verify_message("Test Guild 0")
    await dpytest.kick_callback(test_config.guilds[0], client.user)
    arg = "0"
    for i in range(10):
        guild = dpytest.back.make_guild(f"Test Guild {i}")
        test_config.guilds.append(guild)
        await dpytest.member_join(i, client.user)
        await dpytest.message(KoalaBot.COMMAND_PREFIX + f"servers {arg}", i)
        await dpytest.verify_message("Test Guild 0")
