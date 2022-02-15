#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest
from discord.ext import commands
from sqlalchemy import select

# Own modules
import koalabot
from koala.cogs import Voting
from koala.cogs.voting.models import Votes
from koala.db import session_manager, insert_extension


@pytest.fixture(autouse=True)
def cog(bot: commands.Bot):
    cog = Voting(bot)
    insert_extension("Vote", 0, True, True)
    bot.add_cog(cog)
    dpytest.configure(bot)
    print("Tests starting")
    return cog


@pytest.mark.asyncio
async def test_discord_create_vote():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
        assert dpytest.verify().message().content(
            f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote`"
            f" to see how to configure it.")
        in_db = session.execute(select(Votes.author_id, Votes.guild_id)).first()
        assert in_db
        assert in_db[0] == guild.members[0].id
        assert in_db[1] == guild.id


@pytest.mark.asyncio
async def test_discord_create_vote_wrong():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        session.add(Votes(vote_id=111, author_id=guild.members[0].id, guild_id=guild.id, title="Test Vote"))
        session.commit()
        await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
        assert dpytest.verify().message().content("You already have a vote with title Test Vote sent!")
        await dpytest.message(
            f"{koalabot.COMMAND_PREFIX}vote create aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert dpytest.verify().message().content("Title too long")
        await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote 2")
        assert dpytest.verify().message().content(
            f"Vote titled `Test Vote 2` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` "
            f"to see how to configure it.")
        await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote 3")
        assert dpytest.verify().message().content(
            f"You already have an active vote in {guild.name}. Please send that with `{koalabot.COMMAND_PREFIX}vote "
            f"send` before creating a new one.")


@pytest.mark.asyncio
async def test_discord_vote_add_and_remove_role(cog):
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how "
        f"to configure it.")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote addRole {guild.roles[0].id}")
    assert dpytest.verify().message().content(f"Vote will be sent to those with the {guild.roles[0].name} role")
    vote = cog.vote_manager.get_configuring_vote(guild.members[0].id)
    assert guild.roles[0].id in vote.target_roles
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote removeRole {guild.roles[0].id}")
    assert dpytest.verify().message().content(
        f"Vote will no longer be sent to those with the {guild.roles[0].name} role")
    assert guild.roles[0].id not in vote.target_roles


@pytest.mark.asyncio
async def test_discord_set_chair():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how "
        f"to configure it.")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote setChair {guild.members[0].id}")
    assert dpytest.verify().message().content(f"You have been selected as the chair for vote titled Test Vote")
    assert dpytest.verify().message().content(f"Set chair to {guild.members[0].name}")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote setChair")
    assert dpytest.verify().message().content("Results will be sent to the channel vote is closed in")


@pytest.mark.asyncio
async def test_discord_add_remove_option():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how "
        f"to configure it.")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote addOption test+test")
    assert dpytest.verify().message().content("Option test with description test added to vote")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote addOption testtest")
    assert dpytest.verify().message().content("Example usage: k!vote addOption option title+option description")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote removeOption 1")
    assert dpytest.verify().message().content("Option number 1 removed")


@pytest.mark.asyncio
async def test_discord_cancel_vote():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how "
        f"to configure it.")
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote cancel Test Vote")
    assert dpytest.verify().message().content("Vote Test Vote has been cancelled.")
