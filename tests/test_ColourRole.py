#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
from typing import List

# Libs
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
import discord
# Own modules
import KoalaBot
from cogs import ColourRole
from cogs.ColourRole import ColourRoleDBManager
from utils.KoalaDBManager import KoalaDBManager
from tests.utils import TestUtilsCog

# Constants

# Variables
role_colour_cog: ColourRole.ColourRole = None
utils_cog: TestUtilsCog.TestUtilsCog = None
DBManager = ColourRoleDBManager(KoalaBot.database_manager)
DBManager.create_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global role_colour_cog
    global utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    role_colour_cog = ColourRole.ColourRole(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(role_colour_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


def make_list_of_roles(guild: discord.Guild, length: int) -> List[discord.Role]:
    arr = []
    for i in range(length):
        arr.append(dpytest.back.make_role(f"TestRole{i}", guild))
    return arr


def independent_get_protected_colours(guild_id):
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(f"""SELECT * FROM GuildInvalidCustomColourRoles WHERE guild_id = {guild_id};""")
    if not rows:
        return []
    return [row[1] for row in rows]


def independent_get_colour_change_roles(guild_id):
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(f"""SELECT * FROM GuildColourChangePermissions WHERE guild_id = {guild_id};""")
    if not rows:
        return []
    return [row[1] for row in rows]


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_functions_protected_colour_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = make_list_of_roles(guild, length)
    # Test dbmanager add protected role
    for role in role_list:
        DBManager.add_guild_protected_colour_role(guild.id, role.id)
    protected_role_list = independent_get_protected_colours(guild.id)
    assert protected_role_list == [protected_role.id for protected_role in role_list], [guild_role.id for guild_role in
                                                                                        guild.roles]
    # Test dbmanager get protected roles
    db_get_list = DBManager.get_protected_colour_roles(guild.id)
    assert set(protected_role_list) == set(db_get_list)
    # Test dbmanager remove protected role and teardown test
    for role in role_list:
        DBManager.remove_guild_protected_colour_role(guild.id, role.id)
    assert independent_get_protected_colours(guild.id) == []


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_functions_colour_change_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = make_list_of_roles(guild, length)
    # Test dbmanager add colour change role
    for role in role_list:
        DBManager.add_colour_change_role_perms(guild.id, role.id)
    colour_change_role_list = independent_get_colour_change_roles(guild.id)
    assert colour_change_role_list == [colour_change_role.id for colour_change_role in role_list], [guild_role.id for
                                                                                                    guild_role in
                                                                                                    guild.roles]
    # Test dbmanager get colour change roles
    db_get_list = DBManager.get_colour_change_roles(guild.id)
    assert set(colour_change_role_list) == set(db_get_list)
    # Test dbmanager remove colour change role and teardown test
    for role in role_list:
        DBManager.remove_colour_change_role_perms(guild.id, role.id)
    assert independent_get_colour_change_roles(guild.id) == []


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_no_guild_roles():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    assert not ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_false():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    role = make_list_of_roles(ctx.guild, 1)[0]
    DBManager.add_colour_change_role_perms(ctx.guild.id, role.id)
    assert not ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_true():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    role = make_list_of_roles(ctx.guild, 1)[0]
    member: discord.Member = ctx.author
    DBManager.add_colour_change_role_perms(ctx.guild.id, role.id)
    await member.add_roles(role)
    assert ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.parametrize("hex_str, value",
                         [("000000", 0), ("111111", 1118481), ("228822", 2263074), ("ff82ae", 16745134)])
@pytest.mark.asyncio
async def test_get_colour_from_hex_str(hex_str, value):
    colour: discord.Colour = role_colour_cog.get_colour_from_hex_str(hex_str)
    assert colour.value == value, str(colour.r) + " " + str(colour.g) + " " + str(colour.b) + " " + str(colour.value)


@pytest.mark.asyncio
async def test_command_missing_args():
    assert False


@pytest.mark.asyncio
async def test_command_valid_args():
    assert False


@pytest.mark.asyncio
async def test_command_invalid_args():
    assert False


@pytest.mark.asyncio
async def test_colour_check_valid_colour():
    assert False


@pytest.mark.asyncio
async def test_colour_check_invalid_colour():
    assert False
