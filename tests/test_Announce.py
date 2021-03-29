import random
from typing import *

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
from discord.ext.test import factories as dpyfactory

# Own modules
import KoalaBot
from cogs import Announce
from cogs.Announce import AnnounceDBManager
from tests.utils import TestUtils as utils
from tests.utils import TestUtilsCog
from utils.KoalaDBManager import KoalaDBManager

# Varibales
announce_cog: Announce.Announce = None
utils_cog: TestUtilsCog.TestUtilsCog = None
DBManager = AnnounceDBManager(KoalaBot.database_manager)
DBManager.create_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global announce_cog
    global utils_cog
    bot: commands.Bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    announce_cog = Announce.Announce(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(announce_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


def clean_table():
    announce_cog.announce_database_manager.database_manager.db_execute_commit("DELETE * FROM GuildUsage")


def clean_message_list(guild_id):
    if announce_cog.has_active_msg(guild_id):
        announce_cog.messages.pop(guild_id)
        announce_cog.roles.pop(guild_id)


def make_message(guild):
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    announce_cog.roles[guild.id] = []


@pytest.mark.asyncio
@pytest.mark.skip
async def test_is_allowed_to_create_true():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "announce create")
    assert Announce.Announce.not_exceeded_limit(guild.id)


@pytest.mark.skip
def test_has_active_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    assert (guild.id in announce_cog.messages.keys()) == announce_cog.has_active_msg(guild.id)
    make_message(guild)
    assert announce_cog.messages[guild.id] == announce_cog.has_active_msg(guild.id)


def test_has_no_active_message_initial():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    assert not announce_cog.has_active_msg(guild.id)


# testing creating messages
@pytest.mark.asyncio
async def test_create_legal_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        dpytest.verify_message("Please enter a message")
        dpytest.verify_message(f"An announcement has been created for guild {guild.name}")
        dpytest.verify_embed()
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name


@pytest.mark.asyncio
async def test_create_illegal_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    long_content = ""
    for i in range(2001):
        long_content = long_content + "a"
    long_msg_mock: discord.Message = dpytest.back.make_message(long_content, author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=long_msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        dpytest.verify_message("Please enter a message")
        dpytest.verify_message("The content is more than 2000 characters long, and exceeds the limit")
        assert not announce_cog.has_active_msg(guild.id)


@pytest.mark.asyncio
async def test_create_multiple_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        dpytest.verify_message("Please enter a message")
        dpytest.verify_message(f"An announcement has been created for guild {guild.name}")
        dpytest.verify_embed()
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name

        msg2_mock: discord.Message = dpytest.back.make_message('testMessage2', author, channel)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg2_mock)):
            await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                                  channel=channel)
            dpytest.verify_message("There is currently an active announcement")
            assert announce_cog.has_active_msg(guild.id)
            assert announce_cog.messages[guild.id].description == "testMessage"
            assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name


@pytest.mark.asyncio
async def test_create_message_after_send_before_30_days():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        dpytest.verify_message("Please enter a message")
        dpytest.verify_message(f"An announcement has been created for guild {guild.name}")
        dpytest.verify_embed()
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name
        # sending the message
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        for _ in guild.members:
            dpytest.verify_embed()
        dpytest.verify_message("The announcement was made successfully")
        # try creating another announcement immediately
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg_mock)):
            await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                                  channel=channel)
            dpytest.verify_message("You have recently sent an announcement and cannot use this function for now")
            assert not announce_cog.has_active_msg(guild.id)


@pytest.mark.asyncio
async def test_create_message_timeout():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        dpytest.verify_message("Please enter a message")
        dpytest.verify_message("Okay, I'll cancel the command.")


@pytest.mark.parametrize("command_word, prompt_message", [("changeTitle", "Please enter the new title"),
                                                          ("changeContent", "Please enter the new message"), ("addRole",
                                                                                                              "Please enter the roles you want to tag separated by space"),
                                                          ("add",
                                                           "Please enter the roles you want to tag separated by space"),
                                                          ("remove",
                                                           "Please enter the roles you want to remove separated by space"),
                                                          ("removeRole",
                                                           "Please enter the roles you want to remove separated by space")])
@pytest.mark.asyncio
async def test_other_timeout(command_word, prompt_message):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce ' + command_word,
                              channel=channel)
        dpytest.verify_message(prompt_message)
        dpytest.verify_message("Okay, I'll cancel the command.")


# testing functions with no active message
@pytest.mark.parametrize("command_word",
                         ["changeTitle", "changeContent", "addRole", "add", "remove", "removeRole", "preview", "send",
                          "cancel"])
@pytest.mark.asyncio
async def test_functions_no_active(command_word):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce ' + command_word,
                          channel=channel)
    dpytest.verify_message("There is currently no active announcement")


# testing functions with active message
@pytest.mark.asyncio
async def test_change_title():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild)
    assert announce_cog.has_active_msg(guild.id)
    assert announce_cog.messages[guild.id].description == "testMessage"
    assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name
    msg_mock: discord.Message = dpytest.back.make_message('testTitle', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce changeTitle',
                              channel=channel)
        dpytest.verify_message("Please enter the new title")
        dpytest.verify_embed()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == "testTitle"


@pytest.mark.asyncio
async def test_change_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild)
    assert announce_cog.has_active_msg(guild.id)
    assert announce_cog.messages[guild.id].description == "testMessage"
    assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name
    msg_mock: discord.Message = dpytest.back.make_message('testMessage2', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce changeContent',
                              channel=channel)
        dpytest.verify_message("Please enter the new message")
        dpytest.verify_embed()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage2"
        assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name


@pytest.mark.asyncio
async def test_change_long_message():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild)
    assert announce_cog.has_active_msg(guild.id)
    assert announce_cog.messages[guild.id].description == "testMessage"
    msg = ""
    for i in range(2001):
        msg = msg + 'a'
    msg_mock: discord.Message = dpytest.back.make_message(msg, author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce changeContent',
                              channel=channel)
        dpytest.verify_message("Please enter the new message")
        dpytest.verify_message("The content is more than 2000 characters long, and exceeds the limit")
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"


@pytest.mark.parametrize("number_of_roles", [0, 1])
@pytest.mark.asyncio
async def test_add_possible_role(number_of_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild)
    assert announce_cog.roles[guild.id] == []
    role_list = ""
    role_id_list = []
    for i in range(number_of_roles):
        role_list = role_list + str(roles[i].id) + " "
        role_id_list.append(roles[i].id)
    msg_mock: discord.Message = dpytest.back.make_message(role_list, author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce add',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to tag separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == role_id_list


@pytest.mark.asyncio
async def test_add_non_existent_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message("12345", author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce add',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to tag separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.asyncio
async def test_add_same_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild)
    role_list = str(roles[0].id) + " " + str(roles[0].id)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message(role_list, author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce add',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to tag separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == [roles[0].id]


@pytest.mark.asyncio
async def test_remove_role_from_none():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[0].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to remove separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message("12345", author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to remove separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.asyncio
async def test_remove_existing_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild)
    announce_cog.roles[guild.id] = [roles[0].id]
    assert announce_cog.roles[guild.id] == [roles[0].id]
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[0].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to remove separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.skip
@pytest.mark.asyncio
async def test_remove_non_existent_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild)
    announce_cog.roles[guild.id] = [roles[0].id]
    assert announce_cog.roles[guild.id] == [roles[0].id]
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[1].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        dpytest.verify_message("Please enter the roles you want to remove separated by space")
        dpytest.verify_message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == [roles[0].id]


@pytest.mark.skip
def test_embed_consistent():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    embed: discord.Embed = announce_cog.construct_embed(guild.id)
    assert embed.title == f"This announcement is from {guild.name}"
    assert embed.description == "testMessage"
    assert embed.thumbnail.get("url") == guild.icon_url


@pytest.mark.asyncio
async def test_preview_consistent():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    announce_cog.roles[guild.id] = []
    embed: discord.Embed = announce_cog.construct_embed(guild.id)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce preview',
                          channel=channel)
    dpytest.verify_embed(embed=embed)


@pytest.mark.asyncio
async def test_cancel():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    announce_cog.roles[guild.id] = [123, 234]
    assert guild.id in announce_cog.messages.keys()
    assert guild.id in announce_cog.roles.keys()
    await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce cancel',
                          channel=channel)
    assert guild.id not in announce_cog.messages.keys()
    assert guild.id not in announce_cog.roles.keys()
