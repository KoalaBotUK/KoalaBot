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
import mock
import pytest

# Own modules
import KoalaBot
from cogs import Insights, BaseCog
from tests.utils_testing import LastCtxCog


# Constants

# Variables

@pytest.fixture(scope="function", autouse=True)
def utils_cog(bot):
    utils_cog = LastCtxCog.LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return utils_cog


@pytest.fixture(scope="function", autouse=True)
def base_cog(bot):
    base_cog = BaseCog.BaseCog(bot)
    bot.add_cog(base_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return base_cog


@pytest.fixture(scope="function", autouse=True)
async def insights_cog(bot):
    insights_cog = Insights.Insights(bot)
    bot.add_cog(insights_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return insights_cog


@pytest.mark.asyncio
@pytest.mark.parametrize("num_guilds, num_members",
                         [(1, 1), (1, 2), (1, 10), (2, 2), (2, 5), (2, 20), (5, 100), (100, 10000), (20, 20000)])
async def test_insights(num_guilds, num_members):
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
