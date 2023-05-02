#Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select
from koala.cogs import Voting
from koala.cogs.voting.models import Votes

# Own modules
import koalabot
from koala.db import assign_session, session_manager, insert_extension
from tests.log import logger
from koala.cogs.voting import core


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cog(bot: commands.Bot):
    cog = Voting(bot)
    await bot.add_cog(cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return cog


@pytest.mark.asyncio
async def test_update_vote_message(bot: commands.Bot):
    pass
    # await core.update_vote_message(bot)


def test_create_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    assert core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild) == f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how to configure it."


@pytest.mark.asyncio
async def test_vote_already_created(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")

    assert core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild) == f"You already have an active vote in {guild.name}. Please send that with `{koalabot.COMMAND_PREFIX}vote send` before creating a new one."


@assign_session
@pytest.mark.asyncio
async def test_vote_already_sent(bot: commands.Bot, cog, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    session.add(Votes(vote_id=111, author_id=author.id, guild_id=guild.id, title="Test Vote"))
    session.commit()

    assert core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild) == "You already have a vote with title Test Vote sent!"


@pytest.mark.asyncio
async def test_add_role(bot: commands.Bot, cog, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    role: discord.Role = dpytest.back.make_role("testRole", guild, id_num=555)

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert core.set_roles(cog.vote_manager, author, role, "add") == f"Vote will be sent to those with the {role.name} role"


@pytest.mark.asyncio
async def test_remove_role(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    role: discord.Role = dpytest.back.make_role("testRole", guild, id_num=555)

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    core.set_roles(cog.vote_manager, author, role, "add")
    
    assert core.set_roles(cog.vote_manager, author, role, "remove") == f"Vote will no longer be sent to those with the {role.name} role"


@pytest.mark.asyncio
async def test_set_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert await core.set_chair(cog.vote_manager, author, chair) == f"Set chair to {chair.name}"


# failing because idk how to mock a blocked dm channel
@pytest.mark.asyncio
async def test_set_chair_no_dms(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    # dpytest.back.start_private_message
    with mock.patch('discord.channel.DMChannel', mock.Mock(side_effect=Exception('discord.Forbidden'))):
        with pytest.raises(discord.Forbidden, match="Chair not set as requested user is not accepting direct messages."):
            await core.set_chair(cog.vote_manager, author, chair)


@pytest.mark.asyncio
async def test_set_no_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert await core.set_chair(cog.vote_manager, author) == "Results will be sent to the channel vote is closed in"


# make_voice_channel doesn't exist even though it's in their documentation
@pytest.mark.asyncio
async def test_set_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel = dpytest.back.make_voice_channel("Voice Channel", guild)

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_channel(cog.vote_manager, author, channel) == f"Set target channel to {channel.name}"


@pytest.mark.asyncio
async def test_set_no_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_channel(cog.vote_manager, author) == "Removed channel restriction on vote"