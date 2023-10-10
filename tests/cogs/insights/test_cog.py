#!/usr/bin/env python
"""
Testing KoalaBot Insights Cog
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio

# Own modules
import koalabot
from koala.cogs.insights import cog

# Constants

# Variables


@pytest.mark.asyncio
async def test_setup(bot):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        await cog.setup(bot)
    mock1.assert_called()


@pytest_asyncio.fixture
async def insights_cog(bot: discord.ext.commands.Bot):
    """ setup any state specific to the execution of the given module."""
    insights_cog = cog.Insights(bot)
    await bot.add_cog(insights_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return insights_cog


@pytest.mark.asyncio
@pytest.mark.parametrize("members,guilds", [(0, 0), (10, 10), (100, 100), (1000, 1000)])
async def test_insights(bot, insights_cog, members, guilds):
    for x in range(members):
        await dpytest.member_join(0, name=f"TestUser{x}", discrim={x})

    for x in range(guilds):
        guild = dpytest.backend.make_guild(name=f"FakeGuild{x}")
        dpytest.get_config().guilds.append(guild)
        await dpytest.member_join(guild, dpytest.get_config().client.user)
    
    total_guilds = 1 + guilds
    total_members = 2 + guilds + members
    
    await dpytest.message(koalabot.COMMAND_PREFIX + "insights")

    expected_message = f"Insights:\nThis bot is in a total of {total_guilds} servers." +\
                       f"\nThere are a total of {total_members} members across these servers."

    assert dpytest.verify().message().content(expected_message)


@pytest.mark.asyncio
@pytest.mark.parametrize("total_servers", [0, 50, 500, 1000])
async def test_list_servers(bot, insights_cog, total_servers):
    for x in range(total_servers):
        guild = dpytest.backend.make_guild(name=f"{x}")
        dpytest.get_config().guilds.append(guild)
        await dpytest.member_join(guild, dpytest.get_config().client.user)

    await dpytest.message(koalabot.COMMAND_PREFIX + "servers")

    if total_servers > 0:
        expected_partial_message = "Test Guild 0"
        for x in range(total_servers):
            int_length = len(str(x))
            if len(expected_partial_message) + int_length + 2 > 2000:
                assert dpytest.verify().message().content(expected_partial_message)
                expected_partial_message = str(x)
            else:
                expected_partial_message += f", {x}"
        assert dpytest.verify().message().content(expected_partial_message)
    else:
        assert dpytest.verify().message().content("Test Guild 0")


@pytest.mark.asyncio
@pytest.mark.parametrize("filter_term, expected", [("", "Test Guild 0, this, is, a, list, of, servers"),
                                                   ("s", "Test Guild 0, this, is, list, servers"),
                                                   ("is", "this, is, list"),
                                                   ("hello", """No servers found containing the string "hello".""")])
async def test_list_servers_with_filter(bot, insights_cog, filter_term, expected):
    server_list_names = ["this", "is", "a", "list", "of", "servers"]
    for x in server_list_names:
        guild = dpytest.backend.make_guild(name=x)
        dpytest.get_config().guilds.append(guild)
        await dpytest.member_join(guild, dpytest.get_config().client.user)

    await dpytest.message(koalabot.COMMAND_PREFIX + "servers " + filter_term)

    assert dpytest.verify().message().content(expected)
