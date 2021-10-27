import time

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from koala.cogs import Announce
from tests.tests_utils import LastCtxCog

# Varibales
KoalaBot.is_dpytest = True


@pytest.fixture(autouse=True)
def utils_cog(bot: discord.ext.commands.Bot):
    utils_cog = LastCtxCog.LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return utils_cog


@pytest.fixture(autouse=True)
def announce_cog(bot: discord.ext.commands.Bot):
    announce_cog = Announce.Announce(bot)
    bot.add_cog(announce_cog)
    dpytest.configure(bot, 2, 1, 2)
    print("Tests starting")
    return announce_cog


def clean_message_list(guild_id):
    if announce_cog.has_active_msg(guild_id):
        announce_cog.messages.pop(guild_id)
        announce_cog.roles.pop(guild_id)


def make_message(guild, announce_cog):
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    announce_cog.roles[guild.id] = []


def test_has_active_message(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    assert (guild.id in announce_cog.messages.keys()) == announce_cog.has_active_msg(guild.id)
    make_message(guild, announce_cog)
    assert (guild.id in announce_cog.messages.keys()) == announce_cog.has_active_msg(guild.id)


def test_has_no_active_message_initial(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    assert not announce_cog.has_active_msg(guild.id)


# testing creating messages
@pytest.mark.asyncio
async def test_create_legal_message(bot: discord.Client, announce_cog):
    guild: discord.Guild = bot.guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == ""

#tets dm guild with members who cannot recieve dm's
@pytest.mark.asyncio
async def test_create_message_to_no_dm_user(bot: discord.Client, announce_cog):
    guild: discord.Guild = bot.guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)

    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == ""
        # sending the message
        with mock.patch('discord.Member.send',
                    mock.Mock(side_effect=Exception('AttributeError'))):
            with pytest.raises(discord.ext.commands.errors.CommandInvokeError) as e_info:
                await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',channel=channel)


@pytest.mark.asyncio
async def test_create_illegal_message(announce_cog):
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
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content("The content is more than 2000 characters long, and exceeds the limit")
        assert not announce_cog.has_active_msg(guild.id)


@pytest.mark.asyncio
async def test_create_multiple_message(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == ""

        msg2_mock: discord.Message = dpytest.back.make_message('testMessage2', author, channel)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg2_mock)):
            await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                                  channel=channel)
            assert dpytest.verify().message().content("There is currently an active announcement being created, you can use 'k!announce cancel' "
                                                               "or 'k!announce send' to complete it")
            assert announce_cog.has_active_msg(guild.id)
            assert announce_cog.messages[guild.id].description == "testMessage"
            assert announce_cog.messages[guild.id].title == ""


@pytest.mark.asyncio
async def test_create_message_after_send_before_30_days(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == ""
        # sending the message
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        for _ in guild.members:
            assert dpytest.verify().message()
        assert dpytest.verify().message().content("The announcement was made successfully")
        # try creating another announcement immediately
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg_mock)):
            await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                                  channel=channel)
            assert dpytest.verify().message().content("You have recently sent an announcement and cannot use this function for 30 days")
            assert not announce_cog.has_active_msg(guild.id)

@pytest.mark.asyncio
async def test_create_message_timeout():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content("Okay, I'll cancel the command.")


@pytest.mark.parametrize("command_word, prompt_message", [("changeTitle", "Please enter the new title, I'll wait for 60 seconds, no rush."),
                                                          ("changeContent", "Please enter the new message, I'll wait for 60 seconds, no rush."), ("addRole",
                                                                                                              "Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush."),
                                                          ("add",
                                                           "Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush."),
                                                          ("remove",
                                                           "Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush."),
                                                          ("removeRole",
                                                           "Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")])
@pytest.mark.asyncio
async def test_other_timeout(command_word, prompt_message, announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce ' + command_word,
                              channel=channel)
        assert dpytest.verify().message().content(prompt_message)
        assert dpytest.verify().message().content("Okay, I'll cancel the command.")


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
    assert dpytest.verify().message().content("There is currently no active announcement")


# testing functions with active message
@pytest.mark.asyncio
async def test_change_title(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    assert announce_cog.has_active_msg(guild.id)
    assert announce_cog.messages[guild.id].description == "testMessage"
    assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name
    msg_mock: discord.Message = dpytest.back.make_message('testTitle', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce changeTitle',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the new title, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"
        assert announce_cog.messages[guild.id].title == "testTitle"


@pytest.mark.asyncio
async def test_change_message(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    assert announce_cog.has_active_msg(guild.id)
    assert announce_cog.messages[guild.id].description == "testMessage"
    assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name
    msg_mock: discord.Message = dpytest.back.make_message('testMessage2', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce changeContent',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the new message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage2"
        assert announce_cog.messages[guild.id].title == "This announcement is from " + guild.name


@pytest.mark.asyncio
async def test_change_long_message(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
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
        assert dpytest.verify().message().content("Please enter the new message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content("The content is more than 2000 characters long, and exceeds the limit")
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.messages[guild.id].description == "testMessage"


@pytest.mark.parametrize("number_of_roles", [0, 1])
@pytest.mark.asyncio
async def test_add_possible_role(number_of_roles, announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
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
        assert dpytest.verify().message().content("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == role_id_list

@pytest.mark.asyncio
@pytest.mark.parametrize("number_of_roles", [0, 1])
async def test_send_announce_roles(bot: discord.Client, number_of_roles, announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
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
        assert dpytest.verify().message().content("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == role_id_list
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        for _ in guild.members:
            assert dpytest.verify().message()
        assert dpytest.verify().message().content("The announcement was made successfully")
        
@pytest.mark.asyncio
@pytest.mark.parametrize("number_of_roles", [0, 1])
async def test_send_announce_roles_with_no_dm_user(bot: discord.Client, number_of_roles, announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
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
        assert dpytest.verify().message().content("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == role_id_list
        # sending the message
        with mock.patch('discord.Member.send',
                    mock.Mock(side_effect=Exception('AttributeError'))):
            with pytest.raises(discord.ext.commands.errors.CommandInvokeError) as e_info:
                await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',channel=channel)


@pytest.mark.asyncio
async def test_add_non_existent_role(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message("12345", author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce add',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.asyncio
async def test_add_same_role(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
    role_list = str(roles[0].id) + " " + str(roles[0].id)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message(role_list, author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce add',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == [roles[0].id]


@pytest.mark.asyncio
async def test_remove_role_from_none(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
    assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[0].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []
    msg_mock: discord.Message = dpytest.back.make_message("12345", author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.asyncio
async def test_remove_existing_role(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    roles = guild.roles
    make_message(guild, announce_cog)
    announce_cog.roles[guild.id] = [roles[0].id]
    assert announce_cog.roles[guild.id] == [roles[0].id]
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[0].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == []


@pytest.mark.asyncio
async def test_remove_non_existent_role(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    guild.roles.append(await guild.create_role(name="testrole"))
    assert len(guild.roles) == 2
    roles = guild.roles
    make_message(guild, announce_cog)
    announce_cog.roles[guild.id] = [roles[0].id]
    assert announce_cog.roles[guild.id] == [roles[0].id]
    msg_mock: discord.Message = dpytest.back.make_message(str(roles[1].id), author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce remove',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.roles[guild.id] == [roles[0].id]


def test_embed_consistent(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               guild.icon_url)
    embed: discord.Embed = announce_cog.construct_embed(guild)
    assert embed.title == f"This announcement is from {guild.name}"
    assert embed.description == "testMessage"
    assert embed.thumbnail.url == ''


def test_embed_consistent_with_url(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    announce_cog.messages[guild.id] = Announce.AnnounceMessage(f"This announcement is from {guild.name}",
                                                               "testMessage",
                                                               "test_url")
    embed: discord.Embed = announce_cog.construct_embed(guild)
    assert embed.title == f"This announcement is from {guild.name}"
    assert embed.description == "testMessage"
    assert embed.thumbnail.url == "test_url"


@pytest.mark.asyncio
async def test_preview_consistent(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    embed: discord.Embed = announce_cog.construct_embed(guild)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce preview',
                          channel=channel)
    assert dpytest.verify().message().embed(embed=embed)
    assert dpytest.verify().message()


@pytest.mark.asyncio
async def test_cancel(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    make_message(guild, announce_cog)
    announce_cog.roles[guild.id] = [123, 234]
    assert guild.id in announce_cog.messages.keys()
    assert guild.id in announce_cog.roles.keys()
    await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce cancel',
                          channel=channel)
    assert dpytest.verify().message().content("The announcement was cancelled successfully")
    assert guild.id not in announce_cog.messages.keys()
    assert guild.id not in announce_cog.roles.keys()


def test_receiver_msg(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    make_message(guild, announce_cog)
    assert announce_cog.receiver_msg(
        guild) == f"You are currently sending to Everyone and there are {str(len(guild.members))} receivers"
    announce_cog.roles[guild.id] = [guild.roles[0].id]
    assert announce_cog.receiver_msg(
        guild) == f"You are currently sending to {announce_cog.get_role_names(guild.id, guild.roles)} and there are {str(len(announce_cog.get_receivers(guild.id, guild.roles)))} receivers "


@mock.patch("time.time", mock.MagicMock(return_value=1621679835.9347742))
@pytest.mark.asyncio
async def test_announce_db_first_creation(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    assert announce_cog.announce_database_manager.get_last_use_date(guild.id) is None
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.announce_database_manager.get_last_use_date(guild.id) is None
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        for _ in guild.members:
            assert dpytest.verify().message()
        assert dpytest.verify().message().content("The announcement was made successfully")
        assert int(time.time()) == announce_cog.announce_database_manager.get_last_use_date(guild.id)


@mock.patch("time.time", mock.MagicMock(return_value=1621679123.9347742))
@pytest.mark.asyncio
async def test_announce_db_update_time_from_legal_use(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    assert announce_cog.announce_database_manager.get_last_use_date(guild.id) is None
    announce_cog.announce_database_manager.set_last_use_date(guild.id, int(
        time.time()) - Announce.ANNOUNCE_SEPARATION_DAYS * 24 * 60 * 60 - 1)
    assert announce_cog.announce_database_manager.get_last_use_date(guild.id) == int(
        time.time()) - Announce.ANNOUNCE_SEPARATION_DAYS * 24 * 60 * 60 - 1
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("Please enter a message, I'll wait for 60 seconds, no rush.")
        assert dpytest.verify().message().content(f"An announcement has been created for guild {guild.name}")
        assert dpytest.verify().message()
        assert dpytest.verify().message()
        assert announce_cog.has_active_msg(guild.id)
        assert announce_cog.announce_database_manager.get_last_use_date(guild.id) == int(
            time.time()) - Announce.ANNOUNCE_SEPARATION_DAYS * 24 * 60 * 60 - 1
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        for _ in guild.members:
            assert dpytest.verify().message()
        assert dpytest.verify().message().content("The announcement was made successfully")
        assert int(time.time()) == announce_cog.announce_database_manager.get_last_use_date(guild.id)


@mock.patch("time.time", mock.MagicMock(return_value=1621679124.9347742))
@pytest.mark.asyncio
async def test_announce_db_no_update_time_from_illegal_use(announce_cog):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]
    assert announce_cog.announce_database_manager.get_last_use_date(guild.id) is None
    current_time = int(time.time())
    announce_cog.announce_database_manager.set_last_use_date(guild.id, current_time)
    assert announce_cog.announce_database_manager.get_last_use_date(guild.id) == current_time
    msg_mock: discord.Message = dpytest.back.make_message('testMessage', author, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce create',
                              channel=channel)
        assert dpytest.verify().message().content("You have recently sent an announcement and cannot use this function for 30 days")
        assert not announce_cog.has_active_msg(guild.id)
        assert announce_cog.announce_database_manager.get_last_use_date(guild.id) == current_time
        await dpytest.message(KoalaBot.COMMAND_PREFIX + 'announce send',
                              channel=channel)
        assert dpytest.verify().message().content("There is currently no active announcement")
        assert announce_cog.announce_database_manager.get_last_use_date(guild.id) == current_time
