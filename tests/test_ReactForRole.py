#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
from typing import *
import re
import mock
import asyncio
import random
from string import *
# Libs
import discord.ext.test as dpytest
from discord.ext.test import factories as dpyfactory
import pytest
from discord.ext import commands
import discord
import emoji
# Own modules
import KoalaBot
from cogs import ReactForRole
from cogs.ReactForRole import ReactForRoleDBManager
from utils.KoalaDBManager import KoalaDBManager
from tests.utils import TestUtilsCog

# Constants
unicode_emojis = list(emoji.UNICODE_EMOJI.values())
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


def fake_custom_emoji():
    """
    Creates a fake string representation of a discord custom emoji.
    :return:
    """
    emoji_str = ""
    emoji_str += random.choice(["<a:", "<:"])
    emoji_str += ''.join(random.choice(ascii_letters) for i in range(random.randint(4, 12)))
    emoji_str += f":{dpyfactory.make_id()}>"
    return emoji_str


def fake_unicode_emoji():
    """
    Creates a fake unicode emoji
    :return:
    """
    return random.choice(unicode_emojis)


@pytest.mark.asyncio
async def test_rfr_db_functions_guild_rfr_messages():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    channel: discord.TextChannel = dpytest.get_config().channels[0]
    msg_id = dpyfactory.make_id()
    # Test when no messages exist
    expected_full_list: List[Tuple[int, int, int, int]] = []
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id) == expected_full_list
    assert independent_get_guild_rfr_message() == expected_full_list
    # Test on adding first message, 1 message, 1 channel, 1 guild
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    expected_full_list.append((guild.id, channel.id, msg_id, 1))
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id) == [expected_full_list[0]]
    # 2 guilds, 1 channel each, 2 messages
    guild2: discord.Guild = dpytest.back.make_guild("TestGuild2")
    channel2: discord.TextChannel = dpytest.back.make_text_channel("TestGuild2Channel1", guild2)
    msg_id = dpyfactory.make_id()
    dpytest.get_config().guilds.append(guild2)
    DBManager.add_rfr_message(guild2.id, channel2.id, msg_id)
    expected_full_list.append((guild2.id, channel2.id, msg_id, 2))
    assert independent_get_guild_rfr_message(guild2.id, channel2.id, msg_id) == [expected_full_list[1]]
    assert independent_get_guild_rfr_message(guild2.id, channel2.id, msg_id)[0] == DBManager.get_rfr_message(guild2.id,
                                                                                                             channel2.id,
                                                                                                             msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    # 1 guild, 2 channels with 1 message each
    guild1channel2: discord.TextChannel = dpytest.back.make_text_channel("TestGuild1Channel2", guild)
    msg_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, guild1channel2.id, msg_id)
    expected_full_list.append((guild.id, guild1channel2.id, msg_id, 3))
    assert independent_get_guild_rfr_message(guild.id, guild1channel2.id, msg_id) == [expected_full_list[2]]
    assert independent_get_guild_rfr_message(guild.id, guild1channel2.id, msg_id)[0] == DBManager.get_rfr_message(
        guild.id, guild1channel2.id, msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(guild.id) == [expected_full_list[0], expected_full_list[2]]
    # 1 guild, 1 channel, with 2 messages
    msg_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    expected_full_list.append((guild.id, channel.id, msg_id, 4))
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id) == [expected_full_list[3]]
    assert independent_get_guild_rfr_message(guild.id, channel.id, msg_id)[0] == DBManager.get_rfr_message(guild.id,
                                                                                                           channel.id,
                                                                                                           msg_id)
    assert independent_get_guild_rfr_message() == expected_full_list
    assert independent_get_guild_rfr_message(guild.id, channel.id) == [expected_full_list[0], expected_full_list[3]]
    # remove all messages
    guild_rfr_messages = independent_get_guild_rfr_message()
    for guild_rfr_message in guild_rfr_messages:
        assert guild_rfr_message in guild_rfr_messages
        DBManager.remove_rfr_message(guild_rfr_message[0], guild_rfr_message[1], guild_rfr_message[2])
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
    fake_emoji_1 = fake_unicode_emoji()
    fake_role_id_1 = dpyfactory.make_id()
    expected_full_list.append((1, fake_emoji_1, fake_role_id_1))
    DBManager.add_rfr_message_emoji_role(guild_rfr_message[3], fake_emoji_1, fake_role_id_1)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(1) == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3], fake_emoji_1,
                                                  fake_role_id_1) == [DBManager.get_rfr_reaction_role(
        guild_rfr_message[3], fake_emoji_1, fake_role_id_1)]
    # 1 unicode, 1 custom, trying to get same role
    fake_emoji_2 = fake_custom_emoji()
    DBManager.add_rfr_message_emoji_role(guild_rfr_message[3], fake_emoji_2, fake_role_id_1)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3]) == DBManager.get_rfr_message_emoji_roles(
        guild_rfr_message[3])
    assert [DBManager.get_rfr_reaction_role(guild_rfr_message[3], fake_emoji_2, fake_role_id_1)] == [None]
    # 2 roles, with 1 emoji trying to give both roles
    fake_role_id_2 = dpyfactory.make_id()
    DBManager.add_rfr_message_emoji_role(guild_rfr_message[3], fake_emoji_1, fake_role_id_2)
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(guild_rfr_message[3]) == DBManager.get_rfr_message_emoji_roles(
        guild_rfr_message[3])
    assert [DBManager.get_rfr_reaction_role(guild_rfr_message[3], fake_emoji_1, fake_role_id_2)] == [None]

    # 2 roles, 2 emojis, 1 message. split between them
    fake_emoji_2 = fake_custom_emoji()
    fake_role_id_2 = dpyfactory.make_id()
    expected_full_list.append((1, fake_emoji_2, fake_role_id_2))
    DBManager.add_rfr_message_emoji_role(*expected_full_list[1])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(1, fake_emoji_1) == [(1, fake_emoji_1, fake_role_id_1)]
    assert independent_get_rfr_message_emoji_role(1, fake_emoji_2) == [(1, fake_emoji_2, fake_role_id_2)]
    assert independent_get_rfr_message_emoji_role(1, fake_emoji_1)[0][
               2] == DBManager.get_rfr_reaction_role_by_emoji_str(1,
                                                                  fake_emoji_1)
    assert independent_get_rfr_message_emoji_role(1) == DBManager.get_rfr_message_emoji_roles(1)
    assert independent_get_rfr_message_emoji_role(1, role_id=fake_role_id_2)[0][
               2] == DBManager.get_rfr_reaction_role_by_role_id(1, fake_role_id_2)

    # 2 roles 2 emojis, 2 messages. duplicated messages
    msg2_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg2_id)
    assert independent_get_guild_rfr_message() == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2)]
    guild_rfr_message_2 = independent_get_guild_rfr_message()[1]
    DBManager.add_rfr_message_emoji_role(guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1)
    DBManager.add_rfr_message_emoji_role(guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)
    expected_full_list.extend([(guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1),
                               (guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(2) == DBManager.get_rfr_message_emoji_roles(2)
    assert independent_get_rfr_message_emoji_role(1) == DBManager.get_rfr_message_emoji_roles(1)

    # 2 roles 2 emojis 2 messages. Swapped
    msg3_id = dpyfactory.make_id()
    DBManager.add_rfr_message(guild.id, channel.id, msg3_id)
    assert independent_get_guild_rfr_message() == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2),
                                                   (guild.id, channel.id, msg3_id, 3)]
    guild_rfr_message_3 = independent_get_guild_rfr_message()[2]
    DBManager.add_rfr_message_emoji_role(guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2)
    DBManager.add_rfr_message_emoji_role(guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)
    expected_full_list.extend([(guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2),
                               (guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)])
    assert independent_get_rfr_message_emoji_role() == expected_full_list
    assert independent_get_rfr_message_emoji_role(3) == DBManager.get_rfr_message_emoji_roles(3)
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
        assert row not in independent_get_rfr_message_emoji_role(), independent_get_guild_rfr_message()
    # test deleting just emoji role combos
    rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(2)
    DBManager.remove_rfr_message_emoji_roles(2)
    for row in rfr_message_emoji_roles:
        assert row not in independent_get_rfr_message_emoji_role(), independent_get_guild_rfr_message()
    # test deleteing specific
    rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(1)
    DBManager.remove_rfr_message_emoji_role(1, emoji_raw=rfr_message_emoji_roles[0][1])
    assert (rfr_message_emoji_roles[0][0], rfr_message_emoji_roles[0][1],
            rfr_message_emoji_roles[0][2]) not in independent_get_rfr_message_emoji_role()
    DBManager.remove_rfr_message_emoji_role(1, role_id=rfr_message_emoji_roles[1][2])
    assert (rfr_message_emoji_roles[1][0], rfr_message_emoji_roles[1][1],
            rfr_message_emoji_roles[1][2]) not in independent_get_rfr_message_emoji_role()


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.get_parent_database_manager().clear_all_tables(DBManager.get_parent_database_manager().fetch_all_tables())
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
