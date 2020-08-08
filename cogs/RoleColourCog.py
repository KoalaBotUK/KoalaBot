#!/usr/bin/env python

"""
KoalaBot Cog for guild members wishing to change their role colour
"""

# Futures

# Built-in/Generic Imports

import re

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager


# Constants

# Variables


def is_able_to_change_name_colour(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(KoalaBot.is_owner)
    :param ctx: The context of the message
    :return: True if allowed to change role colour. False otherwise
    """
    roles_allowed = get_roles_allowed_to_change_colour(ctx.guild.id)
    return any(ctx.author.roles) in roles_allowed


def get_roles_allowed_to_change_colour(guild_id: int):
    """
    Function that returns the list of roles in a guild that are allowed to change their name colour
    :param guild_id: The id of the guild from which this method needed to be called
    :return: The list of roles able to change their name colour in the guild
    """
    return []


async def get_invalid_role_colours(guild: discord.Guild):
    """
    Function that returns the list of role colours not allowed for a person wishing to change their colour
    :param guild: The guild to fetch illegal colours
    :return: The list of role colours that aren't allowed
    """
    guild_roles = guild.roles
    illegal_colours = [role.colour for role in guild_roles]
    illegal_colours.append([discord.Color.from_rgb(54, 54, 54), discord.Color.from_rgb(0, 0, 0)])


async def get_discord_colour_from_hex_str(colour_str: str):
    r = int(colour_str[0:2], 16)
    g = int(colour_str[2:4], 16)
    b = int(colour_str[4:], 16)
    return discord.Color.from_rgb(r, g, b)


async def is_custom_colour_valid(ctx, banned_colours, colour_str):
    return


class RoleColourCog(commands.Cog):
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

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="add_colour_change_role")
    async def add_colour_change_role(self, ctx, role_id: int):
        """
        Adds a role in a guild to the list of allowed roles who can change their name colour
        :param ctx: Context of the command
        :param role_id: Role ID to add to the list
        """
        return

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="remove_colour_change_role")
    async def remove_colour_change_role(self, ctx, role_id: int):
        """
        Removes a role in a guild from the list of allowed roles who can change their name colour
        :param ctx: Context of the command
        :param role_id: Role ID to remove from the list
        """
        return

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="list_allowed_colour_change_roles")
    async def list_allowed_colour_change_roles(self, ctx):
        """
        Sends a message with the list of roles currently allowed to manually choose a custom colour to the channel this command is called in
        :param ctx: Context of the command
        """
        return

    # @commands.check(is_able_to_change_name_colour)
    @commands.command(name="custom_colour")
    async def change_colour(self, ctx, colour_str: str):
        """
        Allows a user with colour change perms to change their name colour to a custom colour of their choosing, so long
        as it's not too close to an already existing colour.
        :param ctx:
        :param colour_str:
        :return:
        """
        """
        REGEX USED - ^#([A-Fa-f0-9]{6})$
        """
        colour_str = colour_str.upper()
        if colour_str is None:
            await ctx.send("You have not specified a colour.")
        elif not re.match("^([A-Fa-f0-9]{6})$", colour_str):
            await ctx.send("Invalid string specified, make sure it's a valid colour hex string.")
        else:
            # TODO Need to fix it so that old colour roles are removed from the user
            # First remove any previous custom colour role the user has
            for role in ctx.author.roles:
                if re.match("^KoalaBot\[0x([A-Fa-f0-9]{6})]$", role.name):
                    await ctx.author.remove_roles(role)

            # Second check that if a role is empty, it gets deleted from the server
            empty_colour_roles = [role for role in ctx.guild.roles if
                                  re.match("^KoalaBot\[0x([A-Fa-f0-9]{6})]$", role.name) and len(role.members) == 0]
            for role in empty_colour_roles:
                await role.delete(reason="Pruned, since was a custom colour role with no members")

            # Third check that the colour doesn't already exist in the server, and if so just add the new user to that
            if f"KoalaBot[0x{colour_str}]" in [role.name for role in ctx.guild.roles]:
                # In the case that it does already exist, just add the role to the user
                await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name=f"KoalaBot[0x{colour_str}]"))
            else:
                # In the case that it doesn't exist in the guild, create the role and add it to the user
                created_role = await ctx.guild.create_role(name=f"KoalaBot[0x{colour_str}]",
                                                           colour=await get_discord_colour_from_hex_str(colour_str),
                                                           mentionable=False, hoist=False)
                await ctx.author.add_roles(created_role)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(RoleColourCog(bot))


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

    def add_guild_illegal_custom_colour(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO GuildInvalidCustomColourRoles (guild_id, role_id) VALUES ({guild_id}, {role_id});""")

    def remove_guild_illegal_custom_colour(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            f"""DELETE FROM GuildInvalidCustomColourRoles WHERE guild_id = {guild_id} AND role_id = {role_id};""")
