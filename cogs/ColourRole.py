#!/usr/bin/env python

"""
KoalaBot Cog for guild members wishing to change their role colour
"""

# Futures

# Built-in/Generic Imports

import math
import re
from typing import List, Tuple, Any
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
    allowed_role_ids = cr_database_manager.get_colour_change_roles(ctx.guild.id)
    allowed_set = set(allowed_role_ids)
    author: discord.Member = ctx.author
    author_role_ids = [role.id for role in author.roles]
    author_set = set(author_role_ids)
    return allowed_set & author_set


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

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        protected = self.cr_database_manager.get_protected_colour_roles(role.guild.id)
        if role.id in protected:
            self.cr_database_manager.remove_guild_protected_colour_role(role.guild.id, role.id)
        custom_colour_allowed = self.cr_database_manager.get_colour_change_roles(role.guild.id)
        if role.id in custom_colour_allowed:
            self.cr_database_manager.remove_colour_change_role_perms(role.guild.id, role.id)
        await self.rearrange_custom_colour_role_positions(role.guild)

    def get_colour_from_hex_str(self, colour_str: str) -> discord.Colour:
        r = int(colour_str[:2], 16)
        g = int(colour_str[2:4], 16)
        b = int(colour_str[-2:], 16)
        return discord.Colour.from_rgb(r, g, b)

    @commands.check(is_allowed_to_change_colour)
    @commands.command(name="custom_colour")
    async def custom_colour(self, ctx: commands.Context, colour_str: str):
        """
        Command for a user with the correct role to be able to change their

        :param ctx:
        :param colour_str:
        :return:
        """
        colour_str = colour_str.upper()
        if colour_str == "NO":
            await self.prune_author_old_colour_roles(ctx)
            removed = await ctx.send("Okay, removing your old custom colour role then.")
            if not removed:
                await ctx.send(f"{ctx.author.mention} you don't have any colour roles to remove.")
            await self.prune_guild_empty_colour_roles(ctx)
        elif not ColourRole.is_valid_colour_str(colour_str):
            await ctx.send("Invalid colour string specified, make sure it's a valid colour hex.")
        else:
            colour = self.get_colour_from_hex_str(colour_str)
            # Check if the custom colour is valid
            invalid_colours = self.get_guild_protected_colours(ctx)
            valid_colour_check = ColourRole.is_valid_custom_colour(colour, invalid_colours)
            if not valid_colour_check[0]:
                fail: discord.Colour = valid_colour_check[1]
                await ctx.send(
                    f"Colour chosen was too close to an already protected colour {hex(fail.value)}. Please choose a different colour.")
            else:
                # remove the author's old colour roles
                await self.prune_author_old_colour_roles(ctx)
                # Check if the role exists already
                if ColourRole.role_already_exists(ctx, colour_str):
                    # add that role to the author
                    role = discord.utils.get(ctx.guild.roles, name=f"KoalaBot[0x{colour_str}]")
                    await ctx.author.add_roles(role)
                else:
                    # create the role
                    role: discord.Role = await self.create_custom_colour_role(colour, colour_str, ctx)
                    # add that role to the person
                    await ctx.author.add_roles(role)
                    await ctx.author.add_roles(role)
                await ctx.send(f"Your new custom role colour is {colour_str}, with the role {role.mention}")
                # prune any empty guild colour roles then
                await self.prune_guild_empty_colour_roles(ctx)

    @custom_colour.error
    async def custom_colour_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the required role to use this command.")

    async def prune_author_old_colour_roles(self, ctx: commands.Context) -> bool:
        author: discord.Member = ctx.author
        roles: List[discord.Role] = [role for role in author.roles if
                                     re.match("^KoalaBot\[0x([A-F0-9]{6})\]$", role.name)]
        if not roles:
            KoalaBot.logger.debug(
                f"User {author.id} in guild {ctx.guild.id} changed their colour. Found no old colour roles to prune.")
            return False
        await author.remove_roles(*roles)
        msg = "Removed their roles with role id(s) "
        for i in roles:
            msg += str(i.id)
            msg += ", "
        msg = msg[:-2] + "."
        KoalaBot.logger.debug(
            f"User {author.id} in guild {ctx.guild.id} changed their colour. {msg}")
        return True

    async def prune_guild_empty_colour_roles(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        roles: List[discord.Role] = [role for role in guild.roles if
                                     re.match("^KoalaBot\[0x([A-F0-9]{6})\]$", role.name) and len(role.members) == 0]
        if not roles:
            KoalaBot.logger.debug(f"Found no empty colour roles to prune in guild {guild.id}.")
            return
        msg = "Role IDs were "
        for role in roles:
            msg += str(role.id) + ", "
            await role.delete(reason="Pruned since empty colour role")
        msg = msg[:-2]
        KoalaBot.logger.debug(f"Guild id {guild.id}. Pruned {len(roles)} colour roles with no members. {msg}")

    async def prune_member_old_colour_roles(self, members: List[discord.Member]) -> bool:
        count = 0
        guild = members[0].guild
        msg = "Removed colour roles from members who had held this role previously. These were members "
        for member in members:
            roles: List[discord.Role] = [role for role in member.roles if
                                         re.match("^KoalaBot\[0x([A-F0-9]{6})\]$", role.name)]
            if not roles:
                KoalaBot.logger.debug(
                    f"Guild {member.guild.id} removed a role from their roles allowed to have custom colours. Found no newly illegal custom colour roles to prune from member {member.id}.")
            await member.remove_roles(*roles)
            count += 1
            msg += str(member.id) + ", "
        msg = msg[:-2] + "."
        KoalaBot.logger.debug(
            f"Guild {guild.id} removed a role from their roles allowed to have custom colours. {msg}")
        if count == 0:
            return False
        return True

    async def create_custom_colour_role(self, colour: discord.Colour, colour_str: str,
                                        ctx: commands.Context) -> discord.Role:
        colour_role: discord.Role = await ctx.guild.create_role(name=f"KoalaBot[0x{colour_str}]",
                                                                colour=colour,
                                                                mentionable=False, hoist=False)
        role_pos = self.calculate_custom_colour_role_position(ctx.guild)
        await colour_role.edit(position=role_pos)
        await colour_role.edit(position=role_pos)
        return colour_role

    def calculate_custom_colour_role_position(self, guild: discord.Guild) -> int:
        protected_role_list = self.get_protected_roles(guild)
        sorted_protected_role_list = sorted(protected_role_list, key=lambda x: x.position)
        if sorted_protected_role_list is None:
            role_pos = sorted(guild.roles, key=lambda x: x.position)[0].position - 1
        else:
            role_pos = sorted_protected_role_list[0].position - 1
        if role_pos < 1:
            role_pos = 1
        return role_pos

    async def rearrange_custom_colour_role_positions(self, guild: discord.Guild):
        role_pos = self.calculate_custom_colour_role_position(guild)
        roles: List[discord.Role] = [role for role in guild.roles if
                                     re.match("^KoalaBot\[0x([A-F0-9]{6})\]$", role.name)]
        for role in roles:
            await role.edit(position=role_pos)

    def get_guild_protected_colours(self, ctx: commands.Context) -> List[discord.Colour]:
        return ColourRole.get_protected_colours(self.get_protected_roles(ctx.guild))

    @staticmethod
    def is_valid_colour_str(colour_str: str):
        if re.match("^([A-F0-9]{6})$", colour_str):
            return True
        return False

    @staticmethod
    def get_protected_colours(roles: List[discord.Role]) -> List[discord.Colour]:
        role_colours = [role.colour for role in roles]
        role_colours.extend([discord.Colour.from_rgb(0, 0, 0), discord.Colour.from_rgb(54, 54, 54),
                             discord.Colour.from_rgb(255, 255, 255)])
        return role_colours

    @staticmethod
    def get_rgb_colour_distance(colour1: discord.Colour, colour2: discord.Colour) -> float:

        r_diff = colour2.r - colour1.r
        r_sqr_diff = r_diff ** 2
        g_diff = colour2.g - colour1.g
        g_sqr_diff = g_diff ** 2
        b_diff = colour2.b - colour1.b
        b_sqr_diff = b_diff ** 2
        '''
        # SIMPLE ALGORITHM FOR IT
        dist = math.sqrt(r_sqr_diff + g_sqr_diff + b_sqr_diff)
        '''
        # MORE ACCURATE
        r_avg: float = (colour1.r + colour2.r) / 2
        b_fra = (255 - r_avg) / 256
        r_fra = r_avg / 256
        dist_sqr = ((2 + r_fra) * r_sqr_diff) + (4 * g_sqr_diff) + ((2 + b_fra) * b_sqr_diff)
        dist = math.sqrt(dist_sqr)
        return dist

    @staticmethod
    def is_valid_custom_colour(custom_colour: discord.Colour, protected_colours: List[discord.Colour]) -> Tuple[
        bool, Any]:
        if not protected_colours:
            return True, None
        for protected_colour in protected_colours:
            colour_distance = ColourRole.get_rgb_colour_distance(custom_colour, protected_colour)
            KoalaBot.logger.info(
                f"Colour distance between {hex(custom_colour.value)} and {hex(protected_colour.value)} is {colour_distance}.")
            if colour_distance < 30:
                return False, protected_colour
        return True, None

    @staticmethod
    def role_already_exists(ctx: commands.Context, colour_str: str):
        role_name = f"KoalaBot[0x{colour_str}]"
        guild: discord.Guild = ctx.guild
        return role_name in [role.name for role in guild.roles]

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="list_protected_role_colours")
    async def list_protected_role_colours(self, ctx: commands.Context):
        roles = self.get_protected_roles(ctx.guild)
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

    def get_protected_roles(self, guild: discord.Guild) -> List[discord.Role]:
        role_ids = self.cr_database_manager.get_protected_colour_roles(guild.id)
        print(role_ids)
        if not role_ids:
            return []
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
            await self.rearrange_custom_colour_role_positions(ctx.guild)

    @commands.check(KoalaBot.is_owner)  # TODO Change to is_admin in production
    @commands.command(name="remove_protected_role_colour")
    async def remove_protected_role_colour(self, ctx: commands.Context, *, role_str: str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.remove_guild_protected_colour_role(ctx.guild.id, role.id)
            await ctx.send(f"Removed {role.mention} from the list of roles whose colours are protected.")
            await self.rearrange_custom_colour_role_positions(ctx.guild)

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
            members: List[discord.Member] = role.members
            await self.prune_member_old_colour_roles(members)
            self.cr_database_manager.remove_colour_change_role_perms(ctx.guild.id, role.id)
            await ctx.send(
                f"Removed {role.mention} from the list of roles allowed to have a custom colour. Removed the role members' custom colours too, and pruned empty custom colour roles.")
            await self.prune_guild_empty_colour_roles(ctx)


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

    def get_protected_colour_roles(self, guild_id) -> List[int]:
        rows = self.database_manager.db_execute_select(
            f"""SELECT * from GuildInvalidCustomColourRoles WHERE guild_id = {guild_id};""")
        if rows is None:
            return None
        return [row[1] for row in rows]

    def get_colour_change_roles(self, guild_id) -> List[int]:
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
