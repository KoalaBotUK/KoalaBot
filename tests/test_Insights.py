#!/usr/bin/env python

"""
Testing KoalaBot Insights Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random

# Libs
import discord.ext.test as dpytest
import pytest

# Own modules
import KoalaBot
from cogs import Insights
from utils_testing import LastCtxCog


# Constants

# Variables

@pytest.fixture(scope="function", autouse=False)
def setup(bot):
    utils_cog = LastCtxCog.LastCtxCog(bot)
    insights_cog = Insights.Insights(bot)
    bot.add_cog(utils_cog)
    bot.add_cog(insights_cog)
    print("Tests starting (setup)")
    return bot


@pytest.fixture(scope="function", autouse=False)
def setup_no_conf(bot_no_configure):
    bot = bot_no_configure
    utils_cog = LastCtxCog.LastCtxCog(bot)
    insights_cog = Insights.Insights(bot)
    bot.add_cog(utils_cog)
    bot.add_cog(insights_cog)
    print("Tests starting (setup)")
    return bot


@pytest.mark.asyncio
@pytest.mark.parametrize("num_guilds, num_members",
                         [(1, 1), (1, 2), (1, 10), (2, 2), (2, 5), (2, 20), (5, 100), (100, 10000), (20, 20000)])
async def test_insights(num_guilds, num_members, setup):
    test_config = dpytest.get_config()

    for i in range(num_guilds):
        g = dpytest.back.make_guild(f"TestGuild {i}")
        if test_config.guilds[i] is None:
            test_config.guilds[i] = g
        else:
            test_config.guilds.append(g)

    for i in range(1, num_members):
        m = dpytest.back.make_user(f"TestUser {i}", random.randint(1, 9999))
        dpytest.back.make_member(m, random.choice(test_config.guilds))

    expected_users = 0
    for g in test_config.guilds:
        expected_users += g.member_count

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "insights")
    assert dpytest.verify().message().content(
        f"KoalaBot is in {len(dpytest.get_config().guilds)} servers with a member total of {expected_users}.")


@pytest.mark.asyncio
@pytest.mark.parametrize("num_guilds",
                         [1, 2, 5, 10, 100, 200, 500, 1000, 2000, 5000, 10000])
async def test_servers_no_args(num_guilds, setup_no_conf):
    dpytest.configure(setup_no_conf, num_guilds, 1, 1)
    test_config = dpytest.get_config()

    for i in range(num_guilds):
        g = dpytest.back.make_guild(f"Test Guild {i}")
        if test_config.guilds[i] is None or g.name in [gg.name for gg in test_config.guilds]:
            test_config.guilds[i] = g
        else:
            test_config.guilds.append(g)

    strings_expected = []
    msg = ''
    len_msg = 0
    guild_list_names = [g.name for g in test_config.guilds]
    while len(guild_list_names) != 0:
        length = len(guild_list_names[0])
        if len(msg) + length + 2 > 2000 or len_msg == 100:
            strings_expected.append(msg)
            msg = ''
            len_msg = 0
        else:
            guild = guild_list_names.pop(0)
            msg += guild + ", "
            len_msg += 1
    strings_expected.append(msg[:-2])
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "servers")
    while not dpytest.sent_queue.empty():
        x = (await dpytest.sent_queue.get()).content
        assert x in strings_expected, print(f"content = {x}")
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
@pytest.mark.parametrize("num_guilds",
                         [1, 2, 5, 10, 100, 1000, 10000])
async def test_servers_args(num_guilds, setup_no_conf):
    dpytest.configure(setup_no_conf, num_guilds, 1, 1)
    test_config = dpytest.get_config()

    for i in range(num_guilds):
        g = dpytest.back.make_guild(f"Test Guild {i}")
        if test_config.guilds[i] is None or g.name in [gg.name for gg in test_config.guilds]:
            test_config.guilds[i] = g
        else:
            test_config.guilds.append(g)

    arg = '1'
    print(f"arg={arg}")

    strings_expected = []
    msg = ''
    len_msg = 0
    guild_list_names = []
    async for guild in test_config.client.fetch_guilds():
        if arg is not None:
            if arg.upper() in guild.name.upper().split(" "):
                guild_list_names.append(guild.name)
        else:
            guild_list_names.append(guild.name)

    if len(guild_list_names) == 0:
        strings_expected = [f"No servers with {arg} in their name!"]
    else:
        while len(guild_list_names) != 0:
            length = len(guild_list_names[0])
            if len(msg) + length + 2 > 2000 or len_msg == 100:
                strings_expected.append(msg)
                msg = ''
                len_msg = 0
            else:
                guild = guild_list_names.pop(0)
                msg += guild + ", "
                len_msg += 1
        strings_expected.append(msg[:-2])
    print(strings_expected)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + f"servers {arg}")
    while not dpytest.sent_queue.empty():
        x = (await dpytest.sent_queue.get()).content
        assert x in strings_expected, print(f"content = {x}")
    assert dpytest.verify().message().nothing()
