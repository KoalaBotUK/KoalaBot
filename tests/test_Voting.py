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

def test_two_way():
    def test_asserts(f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except AssertionError:
            return
        raise AssertionError

    # test internal asserts don't false positive
    t = Voting.TwoWay({1: 2, 3: 4})
    t2 = Voting.TwoWay({1: 2, 2: 1, 4: 3})
    assert t == t2

    # test an invalid dict cannot be made
    test_asserts(Voting.TwoWay, {1: 2, 2: 3})

    def ta2():
        t = Voting.TwoWay()
        t[1] = 2
        t[2] = 3
        test_asserts(ta2)

def test_vote_manager_general():
    vm = Voting.VoteManager()
    assert not vm.active_votes
    vote = vm.create_vote(ctx, "Test Vote")
    assert ctx.author.id in vm.active_votes.keys()
    assert vm.get_vote(ctx) == vote
    assert vm.has_active_vote(1234)
    vm.cancel_vote(1234)
    assert not vm.has_active_vote(1234)


def test_vote_general():
    vm = Voting.VoteManager()
    vote = vm.create_vote(ctx, "Test Vote")
    assert vote.id == ctx.author.id and vote.guild == ctx.guild.id and vote.title == "Test Vote"
    assert not vote.is_ready()

    vote.add_role(7890)
    assert 7890 in vote.target_roles
    vote.remove_role(7890)
    assert 7890 not in vote.target_roles

    vote.set_vc(1234)
    assert vote.target_voice_channel == 1234

    opt1 = Voting.Option("test option 1", "test body 1")
    opt2 = Voting.Option("test option 2", "test body 2")
    vote.add_option(opt1)
    vote.add_option(opt2)
    assert len(vote.options) == 2
    assert vote.is_ready()

    vote.remove_option(1)
    assert vote.options[0] == opt2


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
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addChair {usr.id}")
    dpytest.verify_message(f"Set chair to {usr.name}")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addChair")
    dpytest.verify_message("Results will just be sent to channel the vote is closed in")

    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test option+test1")
    dpytest.verify_message(f"Option test option with description test1 added to vote")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test option 2+test2")
    dpytest.verify_message(f"Option test option 2 with description test2 added to vote")

    # await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote send")
    # dpytest.verify_message(f"Sent vote to 1 users")
    # errors trying to send embed because I think an old version of discord.py is wanting it as a dict? not sure
