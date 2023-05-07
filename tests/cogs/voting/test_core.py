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

    # dpytest.back.start_private_message?
    # pytest.raises is NOT the way to go here. the Forbidden is excepted, not thrown.
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
def test_set_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel = dpytest.back.make_voice_channel("Voice Channel", guild)

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_channel(cog.vote_manager, author, channel) == f"Set target channel to {channel.name}"


def test_set_no_channel(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_channel(cog.vote_manager, author) == "Removed channel restriction on vote"


def test_add_option(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.add_option(cog.vote_manager, author, "Option 1+Option description") == "Option Option 1 with description Option description added to vote"

def test_add_option_wrong_formatting(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.add_option(cog.vote_manager, author, "Option 1") == "Example usage: k!vote addOption option title+option description"


def test_add_option_too_many(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    
    x = 0
    while (x < 11):
        core.add_option(cog.vote_manager, author, "more+options")
        x += 1

    assert core.add_option(cog.vote_manager, author, "more options+please?") == "Vote has maximum number of options already (10)"


def test_add_option_too_long(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    test_option = "i am trying to write a lot of words here. needs to be over fifteen thousand words to be exact. but i'm separating it so it does not all get clustered into the same paragraph and become a word soup+i was wrong, it is actually fifteen hundred words. whoever actually reads this will get a little entertainment i hope. is there a better way to test this? probably."
    x = 0
    while (x < 5):
        core.add_option(cog.vote_manager, author, test_option)
        x += 1

    assert core.add_option(cog.vote_manager, author, test_option) == "Option string is too long. The total length of all the vote options cannot be over 1500 characters."


def test_remove_option(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    core.add_option(cog.vote_manager, author, "test+option")

    assert core.remove_option(cog.vote_manager, author, 0) == "Option number 0 removed"


def test_remove_option_bad(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.remove_option(cog.vote_manager, author, 0) == "Option number 0 not found"


def test_set_end_time(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_end_time(cog.vote_manager, author, "2222-12-30 13:30") == "Vote set to end at 2222-12-30 13:30:00 UTC"


def test_set_impossible_end_time(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.set_end_time(cog.vote_manager, author, "2020-01-15 12:50") == "You can't set a vote to end in the past"


def test_preview(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    prev = core.preview(cog.vote_manager, author)
    assert prev[0].title == "Test Vote"


@pytest.mark.asyncio
async def test_cancel_sent_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")

    await core.send_vote(cog.vote_manager, author, guild)

    assert core.cancel_vote(cog.vote_manager, author, "Test Vote") == "Vote Test Vote has been cancelled."


def test_cancel_unsent_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)

    assert core.cancel_vote(cog.vote_manager, author, "Test Vote") == "Vote Test Vote has been cancelled."


@pytest.mark.asyncio
async def test_current_votes(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    
    embed = core.current_votes(author, guild)
    assert embed.title == "Your current votes"


@pytest.mark.asyncio
async def test_close_no_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")

    await core.send_vote(cog.vote_manager, author, guild)

    embed = await core.close(bot, cog.vote_manager, author, "Test Vote")
    assert embed.title == "Test Vote Results:"
    assert embed.fields[0].name == "Option 1"
    assert embed.fields[1].name == "Option 2"


@pytest.mark.asyncio
async def test_close_with_chair(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    chair: discord.Member = guild.members[1]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")
    await core.set_chair(cog.vote_manager, author, chair)

    await core.send_vote(cog.vote_manager, author, guild)

    assert await core.close(bot, cog.vote_manager, author, "Test Vote") == f"Sent results to {chair}"
    

@pytest.mark.asyncio
async def test_send_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")

    # not sure how to assert DM sent

    assert await core.send_vote(cog.vote_manager, author, guild) == "Sent vote to 1 users"


@pytest.mark.asyncio
async def test_send_vote_bad_options(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    
    # no options
    assert await core.send_vote(cog.vote_manager, author, guild) == "Please add more than 1 option to vote for"

    # only 1 option
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    assert await core.send_vote(cog.vote_manager, author, guild) == "Please add more than 1 option to vote for"


@pytest.mark.asyncio
async def test_get_results(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")

    await core.send_vote(cog.vote_manager, author, guild)

    embed = await core.results(bot, cog.vote_manager, author, "Test Vote")
    assert embed.title == "Test Vote Results:"
    assert embed.fields[0].name == "Option 1"
    assert embed.fields[1].name == "Option 2"


@pytest.mark.asyncio
async def test_results_vote_not_sent(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    core.start_vote(bot, cog.vote_manager, "Test Vote", author, guild)
    core.add_option(cog.vote_manager, author, "Option 1+Option description")
    core.add_option(cog.vote_manager, author, "Option 2+Option description2")

    assert await core.results(bot, cog.vote_manager, author, "Test Vote") == "That vote has not been sent yet. Please send it to your audience with k!vote send Test Vote"


@pytest.mark.asyncio
async def test_results_invalid_vote(bot: commands.Bot, cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    with pytest.raises(ValueError, match=f"invalid is not a valid vote title for user {author.name}"):
        await core.results(bot, cog.vote_manager, author, "invalid")