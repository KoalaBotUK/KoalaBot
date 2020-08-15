#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import asyncio

# Libs
import discord.ext.test as dpytest
import discord.ext.test.factories as dpyfactory
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import IntroCog
from utils.KoalaDBManager import KoalaDBManager

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables
intro_cog = None
DBManager = KoalaDBManager("./" + KoalaBot.DATABASE_PATH)
DBManager.create_base_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global intro_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    intro_cog = IntroCog.IntroCog(bot)
    bot.add_cog(intro_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return dpytest.get_config()


# Welcome Message Database Manager Tests

@pytest.mark.parametrize("guild_id, expected", [(101,
                                                 "fake guild welcome message"),
                                                (non_existent_guild_id, None)])
@pytest.mark.asyncio
@pytest.mark.db_manager_functions
async def test_db_manager_fetch_welcome_message(guild_id, expected):
    await add_fake_guild_to_db(101)
    val = DBManager.fetch_guild_welcome_message(guild_id)
    assert val == expected, str(guild_id) + f": {val}"


@pytest.mark.parametrize("guild_id, new_message, expected", [(111, "non-default message", "non-default message"), (
        222, "you're here! you're gonna have fun", "you\'re here! you\'re gonna have fun"), (333, '', ''),
                                                             (444, None, 'None')])
@pytest.mark.asyncio
@pytest.mark.db_manager_functions
async def test_db_manager_update_welcome_message(guild_id, new_message, expected):
    await add_fake_guild_to_db(guild_id)
    DBManager.update_guild_welcome_message(guild_id, new_message)
    await asyncio.sleep(0.2)
    val = DBManager.fetch_guild_welcome_message(guild_id)
    assert val == expected, DBManager.fetch_guild_welcome_message(guild_id)


@pytest.mark.asyncio
@pytest.mark.db_manager_functions
async def test_db_manager_new_guild_welcome_message():
    val = DBManager.new_guild_welcome_message(fake_guild_id)
    assert val == IntroCog.DEFAULT_WELCOME_MESSAGE


@pytest.mark.parametrize("guild_id, expected", [(fake_guild_id, 1), (non_existent_guild_id, 0)])
@pytest.mark.asyncio
@pytest.mark.db_manager_functions
async def test_db_manager_remove_guild_welcome_message(guild_id, expected):
    count = DBManager.remove_guild_welcome_message(guild_id)
    assert count == expected


# Welcome Message Discord-based tests

@pytest.mark.asyncio
async def test_on_guild_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestGuildJoin', id_num=1250)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.3)
    val = DBManager.fetch_guild_welcome_message(1250)
    assert val == IntroCog.DEFAULT_WELCOME_MESSAGE


@pytest.mark.asyncio
async def test_on_guild_remove():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    client = test_config.client
    bot_member = test_config.guilds[0].get_member(client.user.id)
    await dpytest.kick_callback(guild, bot_member)
    val = DBManager.fetch_guild_welcome_message(guild.id)
    assert val is None


@pytest.mark.parametrize("guild_id, expected",
                         [(101, f"fake guild welcome message"), (1250, IntroCog.DEFAULT_WELCOME_MESSAGE),
                          (9999, IntroCog.DEFAULT_WELCOME_MESSAGE)])
@pytest.mark.asyncio
async def test_get_guild_welcome_message(guild_id, expected):
    val = IntroCog.get_guild_welcome_message(guild_id)
    assert val == f"{expected}\r\n{IntroCog.BASE_LEGAL_MESSAGE}", val


@pytest.mark.asyncio
async def test_get_non_bot_members():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = test_config.guilds[0]
    assert len(IntroCog.get_non_bot_members(guild)) == 1, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    await dpytest.member_join()
    assert len(IntroCog.get_non_bot_members(guild)) == 2, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    for i in range(3):
        await dpytest.member_join(name=f'TestUser{str(i)}')
    assert len(IntroCog.get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    print(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in IntroCog.get_non_bot_members(guild)])
    await dpytest.kick_callback(guild, guild.get_member(client.user.id))
    assert len(IntroCog.get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    print(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in IntroCog.get_non_bot_members(guild)])


@pytest.mark.asyncio
async def test_on_member_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestMemberJoin', id_num=1234)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.25)
    welcome_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    dpytest.verify_message(welcome_message)
    DBManager.update_guild_welcome_message(guild.id, 'This is an updated welcome message.')
    await asyncio.sleep(0.25)
    welcome_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    dpytest.verify_message(welcome_message)


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.clear_all_tables(DBManager.fetch_all_tables())
    yield DBManager


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest


async def add_fake_guild_to_db(id=-1):
    if id == 9999:
        return -1
    if id == -1:
        id = dpyfactory.make_id()
    DBManager.remove_guild_welcome_message(id)
    DBManager.db_execute_commit(
        f"INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES ({id}, 'fake guild welcome message');")
    return id
