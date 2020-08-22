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
from utils.KoalaDBManager import KoalaDBManager

# Constants

# Variables


role_colour_cog: ColourRole.ColourRole = None
DBManager = KoalaDBManager("./" + KoalaBot.DATABASE_PATH)
DBManager.create_base_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global role_colour_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    role_colour_cog = ColourRole.ColourRole(bot)
    bot.add_cog(role_colour_cog)
    dpytest.configure(bot)
    print("Tests starting")


def make_list_of_roles(guild: discord.Guild, length: int) -> List[discord.Role]:
    arr = []
    for i in range(length):
        arr.append(dpytest.back.make_role(f"TestRole{i}", guild))
    return arr


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_get_protected_colour_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = make_list_of_roles(guild, length)
    for role in role_list:
        role_colour_cog.cr_database_manager.add_guild_protected_colour_role(guild.id, role.id)
    protected_role_list = role_colour_cog.cr_database_manager.get_colour_change_roles(guild.id)
    assert protected_role_list == [protected_role.id for protected_role in role_list], [guild_role.id for guild_role in
                                                                                        guild.roles]


@pytest.mark.asyncio
async def test_colour_change_perm_check_valid():
    assert False


@pytest.mark.asyncio
async def test_colour_change_perm_check_invalid():
    assert False


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
