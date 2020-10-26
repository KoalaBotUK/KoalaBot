#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
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
from cogs import ReactForRole
from cogs.ReactForRole import ReactForRoleDBManager
from tests.utils import TestUtils as utils
from tests.utils import TestUtilsCog
from utils.KoalaDBManager import KoalaDBManager

# Constants

# Variables
rfr_cog: ReactForRole.ReactForRole = None
utils_cog: TestUtilsCog.TestUtilsCog = None
DBManager = ReactForRoleDBManager(KoalaBot.database_manager)
DBManager.create_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global rfr_cog
    global utils_cog
    bot: commands.Bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    rfr_cog = ReactForRole.ReactForRole(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(rfr_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


def independent_get_guild_rfr_message(guild_id=None, channel_id=None, message_id=None) -> List[
    Tuple[int, int, int, int]]:
    sql_select_str = "SELECT * FROM GuildRFRMessages WHERE "
    if guild_id is not None:
        sql_select_str += f"guild_id = {guild_id} AND "
    if channel_id is not None:
        sql_select_str += f"channel_id = {channel_id} AND "
    if message_id is not None:
        sql_select_str += f"message_id = {message_id} AND "
    if not guild_id and not channel_id and not message_id:
        sql_select_str = sql_select_str[:-7] + ";"
    else:
        sql_select_str = sql_select_str[:-5] + ";"
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(sql_select_str)
    if not rows:
        return []
    return rows


def independent_get_rfr_message_emoji_role(emoji_role_id=None, emoji_raw=None, role_id=None) -> List[
    Tuple[int, str, int]]:
    sql_select_str = "SELECT * FROM RFRMessageEmojiRoles WHERE "
    if emoji_role_id is not None:
        sql_select_str += f"emoji_role_id = {emoji_role_id} AND "
    if emoji_raw is not None:
        sql_select_str += f"emoji_raw = '{emoji_raw}' AND "
    if role_id is not None:
        sql_select_str += f"role_id = {role_id} AND "
    if not emoji_role_id and not emoji_raw and not role_id:
        sql_select_str = sql_select_str[:-7] + ";"
    else:
        sql_select_str = sql_select_str[:-5] + ";"
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(sql_select_str)
    if not rows:
        return []
    return rows


def independent_get_guild_rfr_required_role(guild_id=None, role_id=None) -> List[Tuple[int, int]]:
    sql_select_str = "SELECT * FROM GuildRFRRequiredRoles WHERE "
    if guild_id is not None:
        sql_select_str += f"guild_id = {guild_id} AND "
    if role_id is not None:
        sql_select_str += f"role_id = {role_id} AND "
    if not guild_id and not role_id:
        sql_select_str = sql_select_str[:-7] + ";"
    else:
        sql_select_str = sql_select_str[:-5] + ";"
    rows = DBManager.get_parent_database_manager().db_execute_select(sql_select_str)
    if not rows:
        return []
    return rows


# The below database tests are 2 of the ugliest pieces of code I have ever written. I only ask forgiveness for what you
# see below
@pytest.mark.asyncio
async def test_rfr_db_functions_guild_rfr_messages():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = dpytest.get_config().channels[0]
    msg_id = dpyfactory.make_id()
    # Test when no messages exist
    expected_full_list: List[Tuple[int, int, int, int]] = []
    assert independent_get_guild_rfr_message(
        guild.id, channel.id, msg_id) == expected_full_list
    assert independent_get_guild_rfr_message() == expected_full_list
    # Test on adding first message, 1 message, 1 channel, 1 guild
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    expected_full_list.append((guild.id, channel.id, msg_id, 1))
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id) == [
        expected_full_list[0]]
    # 2 guilds, 1 channel each, 2 messages
    guild2: discord.Guild = dpytest.back.make_guild("TestGuild2")
    channel2: discord.TextChannel = dpytest.back.make_text_channel(
        "TestGuild2Channel1", guild2)
    msg_id = dpyfactory.make_id()
    dpytest.get_config().guilds.append(guild2)
    DBManager.add_rfr_message(guild2.id, channel2.id, msg_id)
    expected_full_list.append((guild2.id, channel2.id, msg_id, 2))
    assert independent_get_guild_rfr_message(guild2.id, channel2.id, msg_id) == [
        expected_full_list[1]]
    assert independent_get_guild_rfr_message(guild2.id, channel2.id, msg_id)[0] == DBManager.get_rfr_message(guild2.id,
                                                                                                             channel2.id,
                                                                                                             msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    # 1 guild, 2 channels with 1 message each
    guild1channel2: discord.TextChannel = dpytest.back.make_text_channel(
        "TestGuild1Channel2", guild)
    msg_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, guild1channel2.id, msg_id)
    expected_full_list.append((guild.id, guild1channel2.id, msg_id, 3))
    assert independent_get_guild_rfr_message(
        guild.id, guild1channel2.id, msg_id) == [expected_full_list[2]]
    assert independent_get_guild_rfr_message(guild.id, guild1channel2.id, msg_id)[0] == DBManager.get_rfr_message(
        guild.id, guild1channel2.id, msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(
        guild.id) == [expected_full_list[0], expected_full_list[2]]
    # 1 guild, 1 channel, with 2 messages
    msg_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    expected_full_list.append((guild.id, channel.id, msg_id, 4))
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id) == [
        expected_full_list[3]]
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id)[0] == DBManager.get_rfr_message(guild.id,
                                                                                                           channel.id,
                                                                                                           msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(guild.id, channel.id) == [
        expected_full_list[0], expected_full_list[3]]
    # remove all messages
    guild_rfr_messages = independent_get_guild_rfr_message()
    for guild_rfr_message in guild_rfr_messages:
        assert guild_rfr_message in guild_rfr_messages
        DBManager.remove_rfr_message(
            guild_rfr_message[0], guild_rfr_message[1], guild_rfr_message[2])
        assert guild_rfr_message not in independent_get_guild_rfr_message()
    assert independent_get_guild_rfr_message() == []


@pytest.mark.asyncio
async def test_rfr_db_functions_rfr_message_emoji_roles():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = dpytest.get_config().channels[0]
    msg_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    guild_rfr_message = independent_get_guild_rfr_message()[0]
    expected_full_list: List[Tuple[int, str, int]] = []
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    # 1 unicode, 1 role
    fake_emoji_1 = utils.fake_unicode_emoji()
    fake_role_id_1 = dpyfactory.make_id()
    expected_full_list.append((1, fake_emoji_1, fake_role_id_1))
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message[3], fake_emoji_1, fake_role_id_1)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(1) == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3], fake_emoji_1,
                                                  fake_role_id_1) == [DBManager.get_rfr_reaction_role(
        guild_rfr_message[3], fake_emoji_1, fake_role_id_1)]
    # 1 unicode, 1 custom, trying to get same role
    fake_emoji_2 = utils.fake_custom_emoji_str_rep()
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message[3], fake_emoji_2, fake_role_id_1)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3]) == DBManager.get_rfr_message_emoji_roles(
        guild_rfr_message[3])
    assert [DBManager.get_rfr_reaction_role(
        guild_rfr_message[3], fake_emoji_2, fake_role_id_1)] == [None]
    # 2 roles, with 1 emoji trying to give both roles
    fake_role_id_2 = dpyfactory.make_id()
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message[3], fake_emoji_1, fake_role_id_2)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3]) == DBManager.get_rfr_message_emoji_roles(
        guild_rfr_message[3])
    assert [DBManager.get_rfr_reaction_role(
        guild_rfr_message[3], fake_emoji_1, fake_role_id_2)] == [None]

    # 2 roles, 2 emojis, 1 message. split between them
    fake_emoji_2 = utils.fake_custom_emoji_str_rep()
    fake_role_id_2 = dpyfactory.make_id()
    expected_full_list.append((1, fake_emoji_2, fake_role_id_2))
    DBManager.add_rfr_message_emoji_role(*expected_full_list[1])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(
        1, fake_emoji_1) == [(1, fake_emoji_1, fake_role_id_1)]
    assert independent_get_rfr_message_emoji_role(
        1, fake_emoji_2) == [(1, fake_emoji_2, fake_role_id_2)]
    assert independent_get_rfr_message_emoji_role(1, fake_emoji_1)[0][
               2] == DBManager.get_rfr_reaction_role_by_emoji_str(1,
                                                                  fake_emoji_1)
    assert independent_get_rfr_message_emoji_role(
        1) == DBManager.get_rfr_message_emoji_roles(1)
    assert independent_get_rfr_message_emoji_role(1, role_id=fake_role_id_2)[0][
               2] == DBManager.get_rfr_reaction_role_by_role_id(1, fake_role_id_2)

    # 2 roles 2 emojis, 2 messages. duplicated messages
    msg2_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg2_id)
    assert independent_get_guild_rfr_message(
    ) == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2)]
    guild_rfr_message_2 = independent_get_guild_rfr_message()[1]
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1)
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)
    expected_full_list.extend([(guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1),
                               (guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(
        2) == DBManager.get_rfr_message_emoji_roles(2)
    assert independent_get_rfr_message_emoji_role(
        1) == DBManager.get_rfr_message_emoji_roles(1)

    # 2 roles 2 emojis 2 messages. Swapped
    msg3_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg3_id)
    assert independent_get_guild_rfr_message() == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2),
                                                   (guild.id, channel.id, msg3_id, 3)]
    guild_rfr_message_3 = independent_get_guild_rfr_message()[2]
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2)
    DBManager.add_rfr_message_emoji_role(
        guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)
    expected_full_list.extend([(guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2),
                               (guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(
        3) == DBManager.get_rfr_message_emoji_roles(3)
    assert [x[2] for x in independent_get_rfr_message_emoji_role(emoji_raw=fake_emoji_1)] == [
        DBManager.get_rfr_reaction_role_by_emoji_str(1, fake_emoji_1),
        DBManager.get_rfr_reaction_role_by_emoji_str(2, fake_emoji_1),
        DBManager.get_rfr_reaction_role_by_emoji_str(3, fake_emoji_1)]
    assert [x[2] for x in independent_get_rfr_message_emoji_role(emoji_raw=fake_emoji_2)] == [
        DBManager.get_rfr_reaction_role_by_emoji_str(1, fake_emoji_2),
        DBManager.get_rfr_reaction_role_by_emoji_str(2, fake_emoji_2),
        DBManager.get_rfr_reaction_role_by_emoji_str(3, fake_emoji_2)]
    # test deletion works from rfr message
    rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(3)
    DBManager.remove_rfr_message(guild.id, channel.id, msg3_id)
    for row in rfr_message_emoji_roles:
        assert row not in independent_get_rfr_message_emoji_role(
        ), independent_get_guild_rfr_message()
    # test deleting just emoji role combos
    rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(2)
    DBManager.remove_rfr_message_emoji_roles(2)
    for row in rfr_message_emoji_roles:
        assert row not in independent_get_rfr_message_emoji_role(
        ), independent_get_guild_rfr_message()
    # test deleteing specific
    rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(1)
    DBManager.remove_rfr_message_emoji_role(
        1, emoji_raw=rfr_message_emoji_roles[0][1])
    assert (rfr_message_emoji_roles[0][0], rfr_message_emoji_roles[0][1],
            rfr_message_emoji_roles[0][2]) not in independent_get_rfr_message_emoji_role()
    DBManager.remove_rfr_message_emoji_role(
        1, role_id=rfr_message_emoji_roles[1][2])
    assert (rfr_message_emoji_roles[1][0], rfr_message_emoji_roles[1][1],
            rfr_message_emoji_roles[1][2]) not in independent_get_rfr_message_emoji_role()


@pytest.mark.asyncio
async def test_rfr_db_functions_guild_rfr_required_roles():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = []
    for i in range(50):
        role: discord.Role = utils.fake_guild_role(guild)
        roles.append(role)
        DBManager.add_guild_rfr_required_role(guild.id, role.id)
        assert [x[1] for x in independent_get_guild_rfr_required_role()] == [x.id for x in roles], i
        assert [x[1] for x in independent_get_guild_rfr_required_role()] == DBManager.get_guild_rfr_required_roles(
            guild.id), i

    while len(roles) > 0:
        role: discord.Role = roles.pop()
        DBManager.remove_guild_rfr_required_role(guild.id, role.id)
        assert [x[1] for x in independent_get_guild_rfr_required_role()] == [x.id for x in roles], len(roles)
        assert [x[1] for x in independent_get_guild_rfr_required_role()] == DBManager.get_guild_rfr_required_roles(
            guild.id), len(roles)


@pytest.mark.asyncio
async def test_get_rfr_message_from_prompts():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    member: discord.Member = config.members[0]
    msg: discord.Message = dpytest.back.make_message(".", member, channel)
    channel_id = msg.channel.id
    msg_id = msg.id

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(546542131)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=None)):
            with pytest.raises(commands.CommandError) as exc:
                await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert str(exc.value) == "Invalid Message ID given."
    with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(msg_id)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=msg)):
            with pytest.raises(commands.CommandError) as exc:
                await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert str(
                exc.value) == "Message ID given is not that of a react for role message."
    DBManager.add_rfr_message(msg.guild.id, channel_id, msg_id)
    with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(msg_id)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=msg)):
            rfr_msg, rfr_msg_channel = await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert rfr_msg.id == msg.id
            assert rfr_msg_channel.id == channel_id


# TODO Actually implement the test.
@pytest.mark.parametrize("num_rows", [0, 1, 2, 20, 100, 250])
@pytest.mark.asyncio
async def test_parse_emoji_and_role_input_str(num_rows):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    for i in range(5):
        input_str = ""
        expected_emoji_list = []
        expected_role_list = []
        for j in range(num_rows):
            fake_emoji = random.choice(
                [utils.fake_guild_emoji(guild), utils.fake_unicode_emoji()])
            expected_emoji_list.append(str(fake_emoji))
            if isinstance(fake_emoji, discord.Emoji):
                fake_emoji_str = random.choice(
                    [fake_emoji.id, fake_emoji.name])
            else:
                fake_emoji_str = fake_emoji
            fake_role = utils.fake_guild_role(guild)
            expected_role_list.append(fake_role)
            fake_role_str = random.choice([fake_role.id, fake_role.name,
                                           fake_role.mention])
            input_str += f"{fake_emoji_str}, {fake_role_str}\n\r"
        emoji_roles_list = await rfr_cog.parse_emoji_and_role_input_str(ctx, input_str, 20)
        for emoji_role in emoji_roles_list:
            assert str(emoji_role[0]) == str(
                expected_emoji_list[emoji_roles_list.index(emoji_role)])
            assert emoji_role[1] == expected_role_list[emoji_roles_list.index(
                emoji_role)]


@pytest.mark.skip("dpytest has non-implemented functionality for construction of guild custom emojis")
@pytest.mark.parametrize("num_rows", [0, 1, 2, 20])
@pytest.mark.asyncio
async def test_parse_emoji_or_roles_input_str(num_rows):
    import emoji
    image = discord.File("utils/discord.png", filename="discord.png")
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    input_str = ""
    expected_list = []
    for j in range(num_rows):
        if random.choice([True, False]):
            if random.choice([True, False]):
                fake_emoji = utils.fake_emoji_unicode()
                input_str += fake_emoji + "\n\r"
                expected_list.append(fake_emoji)
                print(f"Unicode emoji {j} in test {num_rows}: {emoji.emojize(fake_emoji)}")
            else:
                fake_emoji_name = utils.fake_custom_emoji_name_str()
                fake_emoji = await guild.create_custom_emoji(name=fake_emoji_name, image=utils.random_image())
                expected_list.append(fake_emoji)
                input_str += str(fake_emoji) + "\n\r"
                print(f"Custom emoji {j} in test {num_rows}: {str(fake_emoji)}")
        else:
            role_name = utils.fake_custom_emoji_name_str()
            await guild.create_role(name=role_name, mentionable=True, hoist=True)
            fake_role: discord.Role = discord.utils.get(guild.roles, name=role_name)
            expected_list.append(fake_role)
            role_str = str(random.choice([fake_role.name, fake_role.id, fake_role.mention]))
            input_str += role_str + "\n\r"
            print(f"Role {j} in test {num_rows}: {fake_role}")

    print(f"Test {num_rows} input_str")
    print(input_str)
    result_list = await rfr_cog.parse_emoji_or_roles_input_str(ctx, input_str)
    for k in range(len(expected_list)):
        assert str(expected_list[k]) == str(result_list[k])


@pytest.mark.parametrize("msg_content", [None, "", "something", " "])
@pytest.mark.asyncio
async def test_prompt_for_input(msg_content):
    config: dpytest.RunnerConfig = dpytest.get_config()
    author: discord.Member = config.members[0]
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    await dpytest.empty_queue()
    if not msg_content:
        with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message',
                        mock.AsyncMock(return_value=(None, channel))):
            result = await rfr_cog.prompt_for_input(ctx, "test")
            dpytest.verify_message("Please enter test so I can progress further. I'll wait 60 seconds, don't worry.")
            dpytest.verify_message("Okay, I'll cancel the command.")
            assert not result
    else:
        msg: discord.Message = dpytest.back.make_message(content=msg_content, author=author, channel=channel)
        with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message', mock.AsyncMock(return_value=(msg, None))):
            result = await rfr_cog.prompt_for_input(ctx, "test")
            dpytest.verify_message("Please enter test so I can progress further. I'll wait 60 seconds, don't worry.")
            assert result == msg_content


@pytest.mark.asyncio
async def test_overwrite_channel_add_reaction_perms():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    with mock.patch('discord.ext.test.backend.FakeHttp.edit_channel_permissions') as mock_edit_channel_perms:
        calls = []
        for i in range(15):
            role: discord.Role = await guild.create_role(name=f"TestRole{i}", permissions=discord.Permissions.all())
            await rfr_cog.overwrite_channel_add_reaction_perms(guild, channel)
            calls.append(mock.call(channel.id, role.id, 0, 64, 'role', reason=None))
            mock_edit_channel_perms.assert_has_calls(calls, True)


@pytest.mark.parametrize("msg_content", [" ", "something"])
@pytest.mark.asyncio
async def test_wait_for_message_not_none(msg_content):
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    bot: discord.Client = config.client
    import threading
    t2 = threading.Timer(interval=0.1, function=dpytest.message, args=(msg_content))
    t2.start()
    fut = rfr_cog.wait_for_message(bot, ctx)
    t2.join()
    assert fut, dpytest.sent_queue


@pytest.mark.asyncio
async def test_wait_for_message_none():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    bot: discord.Client = config.client
    msg, channel = await rfr_cog.wait_for_message(bot, ctx, 0.2)
    assert not msg
    assert channel == ctx.channel


@pytest.mark.asyncio
async def test_is_user_alive():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message',
                    mock.AsyncMock(return_value=(None, ctx.channel))):
        alive: bool = await rfr_cog.is_user_alive(ctx)
        assert not alive
    with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message', mock.AsyncMock(return_value=('a', None))):
        alive: bool = await rfr_cog.is_user_alive(ctx)
        assert alive


@pytest.mark.asyncio
async def test_get_embed_from_message():
    config: dpytest.RunnerConfig = dpytest.get_config()
    author: discord.Member = config.members[0]
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    test_embed_dict: dict = {'title': 'title', 'description': 'descr', 'type': 'rich', 'url': 'https://www.google.com'}
    bot: discord.Client = config.client
    await bot.http.send_message(channel.id, '', embed=test_embed_dict)
    sent_msg: discord.Message = await dpytest.sent_queue.get()
    msg_mock: discord.Message = dpytest.back.make_message('a', author, channel)
    result = rfr_cog.get_embed_from_message(None)
    assert result is None
    result = rfr_cog.get_embed_from_message(msg_mock)
    assert result is None
    result = rfr_cog.get_embed_from_message(sent_msg)
    assert dpytest.embed_eq(result, sent_msg.embeds[0])


@pytest.mark.asyncio
async def test_get_number_of_embed_fields():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    test_embed_dict: dict = {'title': 'title', 'description': 'descr', 'type': 'rich', 'url': 'https://www.google.com'}
    bot: discord.Client = config.client
    await bot.http.send_message(channel.id, '', embed=test_embed_dict)
    sent_msg: discord.Message = await dpytest.sent_queue.get()
    test_embed: discord.Embed = sent_msg.embeds[0]
    num_fields = 0
    for i in range(20):
        test_embed.add_field(name=f'field{i}', value=f'num{i}')
        num_fields += 1
        assert rfr_cog.get_number_of_embed_fields(test_embed) == num_fields


@pytest.mark.skip('dpytest currently has non-implemented functionality for construction of guild custom emojis')
@pytest.mark.asyncio
async def test_get_first_emoji_from_str():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    guild_emoji = utils.fake_guild_emoji(guild)
    guild_emoji = discord.Emoji(guild=guild, state=None,
                                data={'name': "AAA", 'image': None, 'id': dpyfactory.make_id(),
                                      'require_colons': True, 'managed': False})
    guild._state.store_emoji(guild=guild,
                             data={'name': "AAA", 'image': None, 'id': dpyfactory.make_id(),
                                   'require_colons': True, 'managed': False})
    assert guild_emoji in guild.emojis

    author: discord.Member = config.members[0]
    channel: discord.TextChannel = guild.text_channels[0]
    msg: discord.Message = dpytest.back.make_message(str(guild_emoji), author, channel)
    result = await rfr_cog.get_first_emoji_from_str(ctx, msg.content)
    print(result)
    assert isinstance(result, discord.Emoji), msg.content
    assert guild_emoji == result


@pytest.mark.asyncio
async def test_rfr_create_message():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed_channel: discord.TextChannel = dpytest.back.make_text_channel('EmbedChannel', guild)
    author: discord.Member = config.members[0]
    from utils import KoalaColours
    test_embed = discord.Embed(title="React for Role", description="Roles below!", colour=KoalaColours.KOALA_GREEN)
    test_embed.set_footer(text="ReactForRole")
    test_embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png")
    with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                    mock.AsyncMock(return_value=embed_channel.mention)):
        with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message',
                        mock.AsyncMock(return_value=(None, channel))):
            with mock.patch('cogs.ReactForRole.ReactForRole.is_user_alive', mock.AsyncMock(return_value=True)):
                with mock.patch(
                        'discord.ext.test.backend.FakeHttp.edit_channel_permissions') as mock_edit_channel_perms:
                    with mock.patch('discord.Message.delete') as mock_delete:
                        await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr createMessage")
                        mock_edit_channel_perms.assert_called_once()
                        dpytest.verify_message(
                            "Okay, this will create a new react for role message in a channel of your choice."
                            "\nNote: The channel you specify will have its permissions edited to make it such that members are unable"
                            " to add new reactions to messages, they can only reaction with existing ones. Please keep this in mind, or setup another channel entirely for this.")
                        dpytest.verify_message("This should be a thing sent in the right channel.")
                        dpytest.verify_message(
                            "Okay, what would you like the title of the react for role message to be? Please enter within 30 seconds.")
                        dpytest.verify_message(
                            "Okay, didn't receive a title. Do you actually want to continue? Send anything to confirm this.")
                        dpytest.verify_message(
                            "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr edit commands.")
                        dpytest.verify_message(
                            "Okay, the title of the message will be \"React for Role\". What do you want the description to be?")
                        dpytest.verify_message(
                            "Okay, didn't receive a description. Do you actually want to continue? Send anything to confirm this.")
                        dpytest.verify_message(
                            "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr edit command.")
                        dpytest.verify_message(
                            "Okay, the description of the message will be \"Roles below!\".\n Okay, I'll create the react for role message now.")
                        dpytest.verify_embed()
                        msg = dpytest.sent_queue.get_nowait()
                        assert "You can use the other k!rfr subcommands to change the message and add functionality as required." in msg.content
                        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_rfr_delete_message():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    await dpytest.empty_queue()
    with mock.patch('cogs.ReactForRole.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input', mock.AsyncMock(return_value="Y")):
            with mock.patch('discord.Message.delete') as mock_msg_delete:
                await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr deleteMessage")
                mock_msg_delete.assert_called_once()
                dpytest.verify_message(
                    "Okay, this will delete an existing react for role message. I'll need some details first though.")
                dpytest.verify_message()
                dpytest.verify_message()
                dpytest.verify_message()
                assert not independent_get_guild_rfr_message(guild.id, channel.id, msg_id)


# @pytest.mark.skip("Not implemented yet.")
@pytest.mark.asyncio
async def test_rfr_edit_description():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.description == 'description'
    with mock.patch('cogs.ReactForRole.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                        mock.AsyncMock(side_effect=["new description", "Y"])):
            with mock.patch('cogs.ReactForRole.ReactForRole.get_embed_from_message', return_value=embed):
                await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr edit description")
                assert embed.description == 'new description'
                dpytest.verify_message()
                dpytest.verify_message()
                dpytest.verify_message()


@pytest.mark.asyncio
async def test_rfr_edit_title():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.title == 'title'
    with mock.patch('cogs.ReactForRole.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('cogs.ReactForRole.ReactForRole.prompt_for_input',
                        mock.AsyncMock(side_effect=["new title", "Y"])):
            with mock.patch('cogs.ReactForRole.ReactForRole.get_embed_from_message', return_value=embed):
                await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr edit title")
                assert embed.title == 'new title'
                dpytest.verify_message()
                dpytest.verify_message()
                dpytest.verify_message()


@pytest.mark.asyncio
async def test_rfr_add_roles_to_msg():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    author: discord.Member = config.members[0]
    message: discord.Message = await dpytest.message("rfr")
    msg_id: int = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    input_em_ro_content = ""
    em_list = []
    ro_list = []
    for i in range(5):
        em = utils.fake_unicode_emoji()
        ro = utils.fake_guild_role(guild)
        input_em_ro_content += f"{str(em)}, {ro.id}\n\r"
        em_list.append(em)
        ro_list.append(ro.mention)
    input_em_ro_msg: discord.Message = dpytest.back.make_message(input_em_ro_content, author, channel)

    with mock.patch('cogs.ReactForRole.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('cogs.ReactForRole.ReactForRole.get_embed_from_message', return_value=embed):
            with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message', return_value=(input_em_ro_msg, None)):
                with mock.patch('discord.Embed.add_field') as add_field:
                    await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr addRoles")
                    calls = []
                    for i in range(5):
                        calls.append(mock.call(name=str(em_list[i]), value=ro_list[i], inline=False))
                    add_field.has_calls(calls)


@pytest.mark.asyncio
async def test_rfr_remove_roles_from_msg():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    author: discord.Member = config.members[0]
    message: discord.Message = await dpytest.message("rfr")
    msg_id: int = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    input_em_ro_content = ""
    em_ro_list = []
    for i in range(5):
        em = utils.fake_unicode_emoji()
        ro = utils.fake_guild_role(guild)
        x = random.choice([str(em), str(ro.id)])
        input_em_ro_content += f"{x}\n\r"
        em_ro_list.append(x)
        embed.add_field(name=str(em), value=ro.mention, inline=False)
        DBManager.add_rfr_message_emoji_role(1, str(em), ro.id)

    input_em_ro_msg: discord.Message = dpytest.back.make_message(input_em_ro_content, author, channel)
    with mock.patch('cogs.ReactForRole.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('cogs.ReactForRole.ReactForRole.get_embed_from_message', return_value=embed):
            with mock.patch('cogs.ReactForRole.ReactForRole.wait_for_message', return_value=(input_em_ro_msg, None)):
                with mock.patch('discord.Embed.add_field') as add_field:
                    with mock.patch(
                            'cogs.ReactForRole.ReactForRoleDBManager.remove_rfr_message_emoji_role') as remove_emoji_role:
                        add_field.reset_mock()
                        await dpytest.message(KoalaBot.COMMAND_PREFIX + "rfr removeRoles")
                        add_field.assert_not_called()
                        calls = []
                        for i in range(5):
                            calls.append((1, em_ro_list[i]))
                        remove_emoji_role.has_calls(calls)


# role-check tests
@pytest.mark.parametrize("num_roles, num_required",
                         [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (5, 1), (5, 2), (20, 5)])
@pytest.mark.asyncio
async def test_can_have_rfr_role(num_roles, num_required):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    r_list = []
    for i in range(num_roles):
        role = utils.fake_guild_role(guild)
        r_list.append(role)
    required = random.sample(set(r_list), num_required)
    for r in required:
        DBManager.add_guild_rfr_required_role(guild.id, r.id)
        assert independent_get_guild_rfr_required_role(guild.id, r.id) is not None
    for i in range(num_roles):
        mem_roles = []
        member: discord.Member = await dpytest.member_join()
        for j in range(i):
            mem_roles.append(r_list[j])
            await member.add_roles(r_list[j])

        assert len(mem_roles) == i
        if len(required) == 0:
            assert rfr_cog.can_have_rfr_role(member)
        else:
            assert rfr_cog.can_have_rfr_role(member) == any(
                x in required for x in member.roles), f"\n\r{member.roles}\n\r{required}"


@pytest.mark.skip("No support for reactions")
@pytest.mark.asyncio
async def test_rfr_without_req_role():
    assert False


@pytest.mark.skip("No support for reactions")
@pytest.mark.asyncio
async def test_rfr_with_req_role():
    assert False


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.get_parent_database_manager().clear_all_tables(
        DBManager.get_parent_database_manager().fetch_all_tables())
    yield DBManager


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest
