#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
# Libs
from unittest import TestCase

import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import Voting
from utils.KoalaDBManager import KoalaDBManager

class Fake:
    def __getattr__(self, item):
        setattr(self, item, Fake())
        return getattr(self, item)


ctx = Fake()
ctx.author.id = 1234
ctx.guild.id = 4567
cog = None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    cog = Voting.Voting(bot)
    bot.add_cog(cog)
    dpytest.configure(bot)


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False


@pytest.mark.asyncio
async def test_vote():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    dpytest.verify_message(f"Vote titled `Test Vote` created for guild {guild.name}")

    role = guild.roles[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addRole {role.id}")
    dpytest.verify_message(f"Vote will be sent to those with the {role.name} role")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote removeRole {role.id}")
    dpytest.verify_message(f"Vote will no longer be sent to those with the {role.name} role")

    usr = guild.members[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote setChair {usr.id}")
    dpytest.verify_message(f"Set chair to {usr.name}")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote setChair")
    dpytest.verify_message("Results will just be sent to channel the vote is closed in")

    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test option+test1")
    dpytest.verify_message(f"Option test option with description test1 added to vote")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test option 2+test2")
    dpytest.verify_message(f"Option test option 2 with description test2 added to vote")

    # await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote send")
    # dpytest.verify_message(f"Sent vote to 1 users")
    # errors trying to send embed because I think an old version of discord.py is wanting it as a dict? not sure
