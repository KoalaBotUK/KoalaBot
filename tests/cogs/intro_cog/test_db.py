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
import pytest

# Own modules
from koala import db as koala_db
from koala.cogs.intro_cog import db as intro_db
from koala.cogs.intro_cog.utils import DEFAULT_WELCOME_MESSAGE, BASE_LEGAL_MESSAGE, get_non_bot_members
from .utils import fake_guild_id, non_existent_guild_id, add_fake_guild_to_db
from tests.log import logger

# Constants

# Variables

# Welcome Message Database Manager Tests

@pytest.mark.parametrize("guild_id, expected", [(101,
                                                 "fake guild welcome message"),
                                                (non_existent_guild_id, None)])
@pytest.mark.asyncio
async def test_db_manager_fetch_welcome_message(guild_id, expected):
    await add_fake_guild_to_db(101)
    val = intro_db.fetch_guild_welcome_message(guild_id)
    assert val == expected, str(guild_id) + f": {val}"


@pytest.mark.parametrize("guild_id, new_message, expected", [(111, "non-default message", "non-default message"), (
        222, "you're here! you're gonna have fun", "you\'re here! you\'re gonna have fun"), (333, '', ''),
                                                             (444, None, None)])
@pytest.mark.asyncio
async def test_db_manager_update_welcome_message(guild_id, new_message, expected):
    await add_fake_guild_to_db(guild_id)
    intro_db.update_guild_welcome_message(guild_id, new_message)
    await asyncio.sleep(0.2)
    val = intro_db.fetch_guild_welcome_message(guild_id)
    assert val == expected, intro_db.fetch_guild_welcome_message(guild_id)


@pytest.mark.asyncio
async def test_db_manager_new_guild_welcome_message():
    val = intro_db.new_guild_welcome_message(fake_guild_id)
    assert val == DEFAULT_WELCOME_MESSAGE


@pytest.mark.parametrize("guild_id, expected", [(fake_guild_id, 1), (non_existent_guild_id, 0)])
@pytest.mark.asyncio
async def test_db_manager_remove_guild_welcome_message(guild_id, expected):
    count = intro_db.remove_guild_welcome_message(guild_id)
    assert count == expected


@pytest.mark.asyncio
async def test_on_guild_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestGuildJoin', id_num=1250)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.3)
    val = intro_db.fetch_guild_welcome_message(1250)
    assert val == DEFAULT_WELCOME_MESSAGE


@pytest.mark.asyncio
async def test_on_guild_remove(bot):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    client = test_config.client
    bot_member = test_config.guilds[0].get_member(client.user.id)
    dpytest.backend.delete_member(bot_member)
    val = intro_db.fetch_guild_welcome_message(guild.id)
    assert val is None


@pytest.mark.parametrize("guild_id, expected",
                         [(101, f"fake guild welcome message"), (1250, DEFAULT_WELCOME_MESSAGE),
                          (9999, DEFAULT_WELCOME_MESSAGE)])
@pytest.mark.asyncio
async def test_get_guild_welcome_message(guild_id, expected):
    val = intro_db.get_guild_welcome_message(guild_id)
    assert val == f"{expected}\r\n{BASE_LEGAL_MESSAGE}", val


@pytest.mark.asyncio
async def test_get_non_bot_members():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = test_config.guilds[0]
    assert len(get_non_bot_members(guild)) == 1, [non_bot_member.name for non_bot_member in
                                                  get_non_bot_members(guild)]
    await dpytest.member_join()
    assert len(get_non_bot_members(guild)) == 2, [non_bot_member.name for non_bot_member in
                                                  get_non_bot_members(guild)]
    for i in range(3):
        await dpytest.member_join(name=f'TestUser{str(i)}')
    assert len(get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                  get_non_bot_members(guild)]
    logger.debug(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in get_non_bot_members(guild)])
    dpytest.backend.delete_member(guild.get_member(client.user.id))
    assert len(get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                  get_non_bot_members(guild)]
    logger.debug(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in get_non_bot_members(guild)])


@pytest.mark.asyncio
async def test_on_member_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestMemberJoin', id_num=1234)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.25)
    welcome_message = intro_db.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    assert dpytest.verify().message().content(welcome_message)
    intro_db.update_guild_welcome_message(guild.id, 'This is an updated welcome message.')
    await asyncio.sleep(0.25)
    welcome_message = intro_db.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    assert dpytest.verify().message().content(welcome_message)


@pytest.fixture(scope='session', autouse=True)
def setup_db():

    koala_db.clear_all_tables()
