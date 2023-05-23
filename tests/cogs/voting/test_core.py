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

# Variables
option1 = {'header': 'option1', 'body': 'desc1'}
option2 = {'header': 'option2', 'body': 'desc2'}


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

    assert core.start_vote(bot, "Test Vote", author.id, guild.id) == f"Vote titled `Test Vote` created for guild {guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how to configure it."


@pytest.mark.asyncio
async def test_vote_already_created(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")

    assert core.start_vote(bot, "Test Vote", author.id, guild.id) == f"You already have an active vote in {guild.name}. Please send that with `{koalabot.COMMAND_PREFIX}vote send` before creating a new one."


@assign_session
@pytest.mark.asyncio
async def test_vote_already_sent(bot: commands.Bot, cog, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    session.add(Votes(vote_id=111, author_id=author.id, guild_id=guild.id, title="Test Vote"))
    session.commit()

    assert core.start_vote(bot, "Test Vote", author.id, guild.id) == "You already have a vote with title Test Vote sent!"


@pytest.mark.asyncio
async def test_add_role(bot: commands.Bot, cog, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    role: discord.Role = dpytest.back.make_role("testRole", guild, id_num=555)

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    assert core.set_roles(bot, author.id, guild.id, role.id, "add") == f"Vote will be sent to those with the {role.name} role"


@pytest.mark.asyncio
async def test_remove_role(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    role: discord.Role = dpytest.back.make_role("testRole", guild, id_num=555)

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}vote create Test Vote")
    core.set_roles(bot, author.id, guild.id, role.id, "add")
    
    assert core.set_roles(bot, author.id, guild.id, role.id, "remove") == f"Vote will no longer be sent to those with the {role.name} role"


@pytest.mark.asyncio
async def test_set_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert await core.set_chair(bot, author.id, chair.id) == f"Set chair to {chair.name}"


# failing because idk how to mock a blocked dm channel
@pytest.mark.asyncio
async def test_set_chair_no_dms(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    # dpytest.back.start_private_message?
    # pytest.raises is NOT the way to go here. the Forbidden is excepted, not thrown.
    with mock.patch('discord.channel.DMChannel', mock.Mock(side_effect=Exception('discord.Forbidden'))):
        with pytest.raises(discord.Forbidden, match="Chair not set as requested user is not accepting direct messages."):
            await core.set_chair(bot, author.id, chair.id)


@pytest.mark.asyncio
async def test_set_no_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert await core.set_chair(bot, author.id) == "Results will be sent to the channel vote is closed in"


# make_voice_channel doesn't exist even though it's in their documentation
def test_set_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel = dpytest.back.make_voice_channel("Voice Channel", guild)

    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.set_channel(bot, author.id, channel.id) == f"Set target channel to {channel.name}"


def test_set_no_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.set_channel(bot, author.id) == "Removed channel restriction on vote"


def test_add_option(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.add_option(author.id, option1) == "Option option1 with description desc1 added to vote"

def test_add_option_wrong_formatting(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, "Test Vote", author.id, guild.id)

    option = {'header': 'Option 1'}

    assert core.add_option(author.id, option) == "Option should have both header and body."


def test_add_option_too_many(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, "Test Vote", author.id, guild.id)
    
    x = 0
    while (x < 11):
        core.add_option(author.id, option1)
        x += 1

    assert core.add_option(author.id, option1) == "Vote has maximum number of options already (10)"


def test_add_option_too_long(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    test_option = {'header': "i am trying to write a lot of words here. needs to be over fifteen thousand words to be exact. but i'm separating it so it does not all get clustered into the same paragraph and become a word soup", 'body': 'i was wrong, it is actually fifteen hundred words. whoever actually reads this will get a little entertainment i hope. is there a better way to test this? probably.'}
    x = 0
    while (x < 5):
        core.add_option(author.id, test_option)
        x += 1

    assert core.add_option(author.id, test_option) == "Option string is too long. The total length of all the vote options cannot be over 1500 characters."


def test_remove_option(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    core.add_option(author.id, option1)

    assert core.remove_option(author.id, 0) == "Option number 0 removed"


def test_remove_option_bad(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.remove_option(author.id, 0) == "Option number 0 not found"


def test_set_end_time(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.set_end_time(author.id, "2222-12-30 13:30") == "Vote set to end at 2222-12-30 13:30:00 UTC"


def test_set_impossible_end_time(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.set_end_time(author.id, "2020-01-15 12:50") == "You can't set a vote to end in the past"


def test_preview(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    prev = core.preview(author.id)
    assert prev[0].title == "Test Vote"


@pytest.mark.asyncio
async def test_cancel_sent_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)

    await core.send_vote(bot, author.id, guild.id)

    assert core.cancel_vote(author.id, "Test Vote") == "Vote Test Vote has been cancelled."


def test_cancel_unsent_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)

    assert core.cancel_vote(author.id, "Test Vote") == "Vote Test Vote has been cancelled."


def test_current_votes(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    
    embed = core.current_votes(author.id, guild.id)
    assert embed.title == "Your current votes"


def test_current_votes_no_votes(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    
    embed = core.current_votes(author.id, guild.id)
    assert embed.title == "Your current votes"
    assert embed.description == "No current votes"


@pytest.mark.asyncio
async def test_close_no_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)

    await core.send_vote(bot, author.id, guild.id)

    embed = await core.close(bot, author.id, "Test Vote")
    assert embed.title == "Test Vote Results:"
    assert embed.fields[0].name == "option1"
    assert embed.fields[1].name == "option2"


@pytest.mark.asyncio
async def test_close_with_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)
    await core.set_chair(bot, author.id, chair.id)

    await core.send_vote(bot, author.id, guild.id)

    assert await core.close(bot, author.id, "Test Vote") == f"Sent results to {chair}"
    

@pytest.mark.asyncio
async def test_send_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)

    # not sure how to assert DM sent

    assert await core.send_vote(bot, author.id, guild.id) == "Sent vote to 1 users"


@pytest.mark.asyncio
async def test_send_vote_bad_options(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    
    # no options
    assert await core.send_vote(bot, author.id, guild.id) == "Please add more than 1 option to vote for"

    # only 1 option
    core.add_option(author.id, option1)
    assert await core.send_vote(bot, author.id, guild.id) == "Please add more than 1 option to vote for"


@pytest.mark.asyncio
async def test_get_results(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)

    await core.send_vote(bot, author.id, guild.id)

    embed = await core.results(bot, author.id, "Test Vote")
    assert embed.title == "Test Vote Results:"
    assert embed.fields[0].name == "option1"
    assert embed.fields[1].name == "option2"


@pytest.mark.asyncio
async def test_results_vote_not_sent(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, "Test Vote", author.id, guild.id)
    core.add_option(author.id, option1)
    core.add_option(author.id, option2)

    assert await core.results(bot, author.id, "Test Vote") == "That vote has not been sent yet. Please send it to your audience with k!vote send Test Vote"


@pytest.mark.asyncio
async def test_results_invalid_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    with pytest.raises(ValueError, match=f"invalid is not a valid vote title for user with id {author.id}"):
        await core.results(bot, author.id, "invalid")