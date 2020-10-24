#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import Voting
from utils.KoalaDBManager import KoalaDBManager

# Constants
msg1 = None
msg2 = None
msg3 = None


def get_test_vote(vote_cog, config):
    return vote_cog.vote_manager.active_votes[config.members[0].id]

# Variables


# Test TwitchAlert
@pytest.fixture
async def vote_cog():
    global msg1, msg2, msg3
    """ setup any state specific to the execution of the given module."""
    KoalaBot.is_dpytest = True
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    vote_cog = Voting.Voting(bot)
    bot.add_cog(vote_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    config = dpytest.get_config()
    msg1 = dpytest.back.make_message(content="no", channel=config.channels[0], author=config.members[0])
    msg2 = dpytest.back.make_message(content="no", channel=config.channels[0], author=config.members[0])
    msg3 = dpytest.back.make_message(content="no", channel=config.channels[0], author=config.members[0])
    print("Tests starting")
    return vote_cog

@pytest.mark.asyncio
async def test_test(vote_cog):
    assert vote_cog

# currently broken
@pytest.mark.asyncio
async def test_example_vote(vote_cog):
    config = dpytest.get_config()
    with mock.patch('cogs.Voting.Voting.wait_for_message', side_effect=[msg1, msg2, msg3]):
        with mock.patch('discord.Message.edit') as mock_edit:
            await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create test")
            dpytest.verify_message(text="""```You have started making a vote titled 'test'.
Each upcoming prompt has a 60 second timeout.
Do you want this vote to be sent to users with specific roles? If so ping each role you want (e.g. @student @staff). If not, reply 'no'.```""")
            mock_edit.assert_called()
            assert vote_cog.vote_manager.vote_exists(config.members[0].id)
        with mock.patch('discord.Message.edit') as mock_edit:
            await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test1+test2")
            mock_edit.assert_called()
            await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test3+test4")
            mock_edit.assert_called()
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote send")
        await dpytest.verify_message("This vote has been sent out to 1 people")

#works but i tried to combine it into the first one along with testing the send
# @pytest.mark.asyncio
# async def test_addOption(vote_cog):
#     with mock.patch('cogs.Voting.Voting.wait_for_message', side_effect=[msg1, msg2, msg3]):
#         with mock.patch('discord.Message.edit') as mock_edit:
#             await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create test")
#             dpytest.verify_message(text="""```You have started making a vote titled 'test'.
# Each upcoming prompt has a 60 second timeout.
# Do you want this vote to be sent to users with specific roles? If so ping each role you want (e.g. @student @staff). If not, reply 'no'.```""")


@pytest.mark.asyncio
async def test_cancel(vote_cog):
    config = dpytest.get_config()
    with mock.patch('cogs.Voting.Voting.wait_for_message', side_effect=[msg1, msg2, msg3]):
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create test")
        dpytest.verify_message(text="""```You have started making a vote titled 'test'.
Each upcoming prompt has a 60 second timeout.
Do you want this vote to be sent to users with specific roles? If so ping each role you want (e.g. @student @staff). If not, reply 'no'.```""")
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote cancel")
        dpytest.verify_message("Your active vote has been cancelled")
        assert config.members[0].id not in vote_cog.vote_manager.active_votes.keys()
