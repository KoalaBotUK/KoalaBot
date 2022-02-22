#!/usr/bin/env python

"""
KoalaBot Cog for guild members wishing to change their role colour
"""

# Futures

# Built-in/Generic Imports
from typing import List, Optional

# Own modules
from koala.db import session_manager

# Libs
from sqlalchemy import select, delete, and_

# Own modules
from .models import GuildColourChangePermissions, GuildInvalidCustomColourRoles


# Variables


class ColourRoleDBManager:
    """
    A class for interacting with the Koala Colour Role database
    """

    def add_colour_change_role_perms(self, guild_id, role_id):
        with session_manager() as session:
            new = GuildColourChangePermissions(guild_id=guild_id, role_id=role_id)
            session.add(new)
            session.commit()

    def remove_colour_change_role_perms(self, guild_id, role_id):
        with session_manager() as session:
            session.execute(
                delete(GuildColourChangePermissions)
                .where(
                    and_(GuildColourChangePermissions.guild_id == guild_id,
                         GuildColourChangePermissions.role_id == role_id)))
            session.commit()

    def add_guild_protected_colour_role(self, guild_id, role_id):
        with session_manager() as session:
            new = GuildInvalidCustomColourRoles(guild_id=guild_id, role_id=role_id)
            session.add(new)
            session.commit()

    def remove_guild_protected_colour_role(self, guild_id, role_id):
        with session_manager() as session:
            session.execute(
                delete(GuildInvalidCustomColourRoles)
                .where(
                    and_(GuildInvalidCustomColourRoles.guild_id == guild_id,
                         GuildInvalidCustomColourRoles.role_id == role_id)))
            session.commit()

    def get_protected_colour_roles(self, guild_id) -> Optional[List[int]]:
        with session_manager() as session:
            colour_roles = session.execute(select(GuildInvalidCustomColourRoles)
                                           .filter_by(guild_id=guild_id)).scalars().all()
            if colour_roles:
                return [colour_role.role_id for colour_role in colour_roles]
            else:
                return []

    def get_colour_change_roles(self, guild_id) -> Optional[List[int]]:
        with session_manager() as session:
            colour_roles = session.execute(select(GuildColourChangePermissions)
                                           .filter_by(guild_id=guild_id)).scalars().all()
            if colour_roles:
                return [colour_role.role_id for colour_role in colour_roles]
            else:
                return []
