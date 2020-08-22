#!/usr/bin/env python

"""
KoalaBot Cog for guild members wishing to change their role colour
"""

# Futures

# Built-in/Generic Imports

import math
import re
from typing import List

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
# Variables
from utils.KoalaDBManager import KoalaDBManager


# Constants

def is_allowed_to_change_colour(ctx: commands.Context):
    cr_database_manager = ColourRoleDBManager(KoalaBot.database_manager)
    allowed_roles = cr_database_manager.get_colour_change_roles(ctx.guild.id)
    return commands.has_any_role(allowed_roles)


class ColourRole(commands.Cog):
    """
        A discord.py cog with general commands useful to managers of the bot and servers
    """

    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("ColourRole", 1, False, True)
        self.cr_database_manager = ColourRoleDBManager(KoalaBot.database_manager)
        self.cr_database_manager.create_tables()

        
    def get_colour_from_hex_str(self, colour_str: str) -> discord.Colour:

        colour_str = colour_str.upper()
        return discord.Colour.from_rgb(1, 1, 1)

    @commands.check(is_allowed_to_change_colour)
    @commands.command(name="custom_colour")
    async def custom_colour(self, ctx: commands.Context, colour_str: str):
        return

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="list_protected_role_colours")
    async def list_protected_role_colours(self, ctx: commands.Context):
        roles = self.get_protected_roles(ctx)
        print(roles)
        msg = "Roles whose colour is protected are:\r\n"
        for role in roles:
            msg += f"{role.mention}\n"
        await ctx.send(msg[:-1])

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="list_custom_colour_allowed_roles")
    async def list_custom_colour_allowed_roles(self, ctx: commands.Context):
        roles = self.get_custom_colour_allowed_roles(ctx)
        print(roles)
        msg = "Roles allowed to have a custom colour are:\r\n"
        for role in roles:
            msg += f"{role.mention}\n"
        await ctx.send(msg[:-1])

    def get_custom_colour_allowed_roles(self, ctx: commands.Context) -> List[discord.Role]:
        role_ids = self.cr_database_manager.get_colour_change_roles(ctx.guild.id)
        print(role_ids)
        if not role_ids:
            return []
        guild: discord.Guild = ctx.guild
        roles = [guild.get_role(role_id) for role_id in role_ids]
        return roles

    def get_protected_roles(self, ctx: commands.Context) -> List[discord.Role]:
        role_ids = self.cr_database_manager.get_protected_colour_roles(ctx.guild.id)
        print(role_ids)
        if not role_ids:
            return []
        guild: discord.Guild = ctx.guild
        roles = [guild.get_role(role_id) for role_id in role_ids]
        return roles

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="add_protected_role_colour")
    async def add_protected_role_colour(self, ctx: commands.Context, *, role_str: str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.add_guild_protected_colour_role(ctx.guild.id, role.id)
            await ctx.send(f"Added {role.mention} to the list of roles whose colours are protected.")

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="remove_protected_role_colour")
    async def remove_protected_role_colour(self, ctx: commands.Context, *, role_str: str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.remove_guild_protected_colour_role(ctx.guild.id, role.id)
            await ctx.send(f"Removed {role.mention} from the list of roles whose colours are protected.")

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="add_custom_colour_allowed_role")
    async def add_custom_colour_allowed_role(self, ctx: commands.Context, *, role_str: str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.add_colour_change_role_perms(ctx.guild.id, role.id)
            await ctx.send(f"Added {role.mention} to the list of roles allowed to have a custom colour.")

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="remove_custom_colour_allowed_role")
    async def remove_custom_colour_allowed_role(self, ctx: commands.Context, *, role_str: str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.remove_colour_change_role_perms(ctx.guild.id, role.id)
            await ctx.send(f"Removed {role.mention} from the list of roles allowed to have a custom colour.")


class ColourRoleDBManager:
    """
    A class for interacting with the Koala Colour Role database
    """

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager = database_manager

    def get_parent_database_manager(self):
        return self.database_manager

    def create_tables(self):
        """
        Creates all the tables associated with the Custom Colour Role extension
        """
        # GuildColourChangePermissions
        sql_create_guild_colour_change_permissions_table = """
        CREATE TABLE IF NOT EXISTS GuildColourChangePermissions (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        PRIMARY KEY (guild_id, role_id),
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        );"""

        # GuildInvalidCustomColours
        sql_create_guild_colour_change_invalid_colours_table = """
        CREATE TABLE IF NOT EXISTS GuildInvalidCustomColourRoles (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        PRIMARY KEY (guild_id, role_id),
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        );"""

        # Create Tables
        self.database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)
        self.database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)

    def add_colour_change_role_perms(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO GuildColourChangePermissions (guild_id, role_id) VALUES ({guild_id}, {role_id});""")

    def remove_colour_change_role_perms(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""DELETE FROM GuildColourChangePermissions WHERE guild_id = {guild_id} AND role_id = {role_id};""")

    def add_guild_protected_colour_role(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO GuildInvalidCustomColourRoles (guild_id, role_id) VALUES ({guild_id}, {role_id});""")

    def remove_guild_protected_colour_role(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""DELETE FROM GuildInvalidCustomColourRoles WHERE guild_id = {guild_id} AND role_id = {role_id};""")

    def get_protected_colour_roles(self, guild_id):
        rows = self.database_manager.db_execute_select(
            f"""SELECT * from GuildInvalidCustomColourRoles WHERE guild_id = {guild_id};""")
        if rows is None:
            return None
        return [row[1] for row in rows]

    def get_colour_change_roles(self, guild_id):
        rows = self.database_manager.db_execute_select(
            f"""SELECT * from GuildColourChangePermissions WHERE guild_id = {guild_id};""")
        if rows is None:
            return None
        return [row[1] for row in rows]


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(ColourRole(bot))
