#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
from typing import *

import discord
# Libs
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
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
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


@pytest.mark.skip("dpytest has no in-built image support for emoji")
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
                fake_emoji = await guild.create_custom_emoji(name=fake_emoji_name, image="attachment://discord.png")
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
    pass


@pytest.mark.asyncio
async def test_overwrite_channel_add_reaction_perms():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    member: discord.Member = config.members[0]
    with mock.patch('discord.ext.test.backend.FakeHttp.edit_channel_permissions') as mock_edit_channel_perms:
        calls = []
        for i in range(15):
            role: discord.Role = await guild.create_role(name=f"TestRole{i}", permissions=discord.Permissions.all())
            await rfr_cog.overwrite_channel_add_reaction_perms(guild, channel)
            calls.append(mock.call(channel.id, role.id, 0, 64, 'role', reason=None))
            mock_edit_channel_perms.assert_has_calls(calls, True)


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
