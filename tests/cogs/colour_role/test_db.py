#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
import discord.ext.test as dpytest
import pytest
from sqlalchemy import delete

from koala.cogs.colour_role.models import GuildColourChangePermissions, GuildInvalidCustomColourRoles
# Own modules
from koala.db import session_manager
from .utils import make_list_of_roles, independent_get_colour_change_roles, independent_get_protected_colours, \
    DBManager


# Constants

# Variables


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_functions_protected_colour_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = await make_list_of_roles(guild, length)
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
    role_list = await make_list_of_roles(guild, length)
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

@pytest.fixture(scope='session', autouse=True)
def setup_db():
    with session_manager() as session:
        session.execute(delete(GuildColourChangePermissions))
        session.execute(delete(GuildInvalidCustomColourRoles))
        session.commit()