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
COLOUR_ROLE_NAMING = r"^KoalaBot\x5B0x[A-F0-9]{6}\x5D$"

def is_allowed_to_change_colour(ctx: commands.Context):
    """
    Command check to see if someone can use the custom_colour command

    :param ctx: Context of the command
    :return: True if the command invoker has a role in the list of roles that are allowed to use the command, False
    otherwise. Always False if there's no roles that have been granted permission to use the command
    """
    if isinstance(ctx.channel, discord.DMChannel):
        return False
    cr_database_manager = ColourRoleDBManager(KoalaBot.database_manager)
    allowed_role_ids = cr_database_manager.get_colour_change_roles(ctx.guild.id)
    allowed_set = set(allowed_role_ids)
    author: discord.Member = ctx.author
    author_role_ids = [role.id for role in author.roles]
    author_set = set(author_role_ids)
    return allowed_set & author_set

def colour_is_enabled(ctx):
    """
    A command used to check if the guild has enabled twitch alert
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "ColourRole")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)

class ColourRole(commands.Cog):
    """
        A discord.py cog with commands to allow server members to change their display name colours to something of their choosing.
    """

    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        KoalaBot.database_manager.insert_extension("ColourRole", 0, True, True)
        self.cr_database_manager = ColourRoleDBManager(KoalaBot.database_manager)
        self.cr_database_manager.create_tables()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """
        Listens for roles being deleted in a guild. On a role being deleted, it automatically removes the role from the
        relevant database tables if it was protected or a permission role for using custom_colour, and reshuffles a
        guild's custom colour roles to ensure people who are still allowed to may keep their custom colour.

        :param role: Role that was deleted from the guild
        """
        protected = self.cr_database_manager.get_protected_colour_roles(role.guild.id)
        if role.id in protected:
            self.cr_database_manager.remove_guild_protected_colour_role(role.guild.id, role.id)
        custom_colour_allowed = self.cr_database_manager.get_colour_change_roles(role.guild.id)
        if role.id in custom_colour_allowed:
            self.cr_database_manager.remove_colour_change_role_perms(role.guild.id, role.id)
        await self.rearrange_custom_colour_role_positions(role.guild)

    def get_colour_from_hex_str(self, colour_str: str) -> discord.Colour:
        """
        Parses a length 6 hex string and returns a Discord.Colour made from that string.

        :param colour_str: Hex string of colour
        :return: Colour from colour_str
        """
        r = int(colour_str[:2], 16)
        g = int(colour_str[2:4], 16)
        b = int(colour_str[-2:], 16)
        return discord.Colour.from_rgb(r, g, b)

    @commands.cooldown(1, 15, commands.BucketType.member)
    @commands.check(is_allowed_to_change_colour)
    @commands.check(colour_is_enabled)
    @commands.command(name="customColour", aliases=["custom_colour", "customColor", "custom_color"])
    async def custom_colour(self, ctx: commands.Context, colour_str: str):
        """
        For a user with the correct role to be able to change their display colour in a guild.
        Syntax is k!custom_colour ("no" / colour hex). Usage with no removes any custom colour held before.
        Won't accept it if the colour chosen too closely resembles a role that was protected's colour or a discord
        blocked colour. A role must be made and that role be added to the permissions by usage of
        k!add_custom_colour_allowed_role <role>, and the command invoker must have that role before they can use this
        command. Has a 15 second cooldown.

        :param ctx: Context of the command
        :param colour_str: The colour hex string specified, or "no" in case of cancelling colour
        """
        colour_str = colour_str.upper()
        if colour_str == "NO":
            removed = await self.prune_author_old_colour_roles(ctx)
            await ctx.send("Okay, removing your old custom colour role then, if you have one.")
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
                await ctx.send(f"Your new custom role colour is #{colour_str}, with the role {role.mention}")
                # prune any empty guild colour roles then
                await self.prune_guild_empty_colour_roles(ctx)

    @custom_colour.error
    async def custom_colour_error(self, ctx: commands.Context, error):
        """
        Catches any error from using the command custom_colour. Only has special case for CheckFailure. Others are
        logged, and a contact support message sent.

        :param ctx: Context of the command
        :param error: Error that occurred
        """
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the required role to use this command.")
        else:
            import time
            KoalaBot.logger.error(f"Unexpected error occurred in Guild {ctx.guild.id}, channel {ctx.channel.id}. "
                                  f"Error was of type {str(type(error))}. Cause was {error.__cause__}.")
            await ctx.send(
                f"Unexpected error occurred. Please contact bot developers with the timestamp {time.time()}, "
                f"guild ID {ctx.guild.id} and Error type {str(type(error))}")

    async def prune_author_old_colour_roles(self, ctx: commands.Context) -> bool:
        """
        Removes any old custom colour roles from the author/invoker of the command if they have any.

        :param ctx: Context of the command
        :return: True if a role was removed. False otherwise.
        """
        author: discord.Member = ctx.author
        roles: List[discord.Role] = [role for role in author.roles if
                                     re.match(COLOUR_ROLE_NAMING, role.name)]
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
        """
        Removes custom colour roles from the command context's guild if they've got no members with that role.

        :param ctx: Context of the command
        """
        guild: discord.Guild = ctx.guild
        roles: List[discord.Role] = [role for role in guild.roles if
                                     re.match(COLOUR_ROLE_NAMING, role.name) and len(role.members) == 0]
        if not roles:
            KoalaBot.logger.debug(f"Found no empty colour roles to prune in guild {guild.id}.")
        else:
            msg = "Role IDs were "
            for role in roles:
                msg += str(role.id) + ", "
                await role.delete(reason="Pruned since empty colour role")
            msg = msg[:-2]
            KoalaBot.logger.debug(f"Guild id {guild.id}. Pruned {len(roles)} colour roles with no members. {msg}")

    async def prune_members_old_colour_roles(self, members: List[discord.Member]) -> bool:
        """
        Removes custom colour roles from a list of members, for example if they all lost permission to have a custom
        colour if the list of roles allowed to have a custom colour changed.

        :param members: List of members whose custom colour roles should be removed
        :return: True if removed at least 1 member's role, or no members had that role in the first place. False
        otherwise.
        """
        if len(members) == 0:
            return True
        count = 0
        m: discord.Member = members[0]
        guild: discord.Guild = m.guild
        msg = "Removed colour roles from members who had held this role previously. These were members "
        for member in members:
            roles: List[discord.Role] = [role for role in member.roles if
                                         re.match(COLOUR_ROLE_NAMING, role.name)]
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
        """
        Creates a custom colour role in the context's guild, with an auto-generated name.

        :param colour: Colour of the role
        :param colour_str: Hex string value of the role colour
        :param ctx: Context of the command
        :return: The role that was created
        """
        colour_role: discord.Role = await ctx.guild.create_role(name=f"KoalaBot[0x{colour_str}]",
                                                                colour=colour,
                                                                mentionable=False, hoist=False)
        role_pos = self.calculate_custom_colour_role_position(ctx.guild)
        await colour_role.edit(position=role_pos)
        await colour_role.edit(position=role_pos)
        return colour_role

    def calculate_custom_colour_role_position(self, guild: discord.Guild) -> int:
        """
        Calculates the position a custom role colour should be to ensure it's shown on people's display names correctly.
        In most cases, it'll be 1 position lower than the lowest positioned protected role.

        :param guild: Guild to calculate for
        :return: Role position custom colour roles should be in.
        """
        protected_role_list: List[discord.Role] = self.get_protected_roles(guild)
        if len(guild.roles) == 0:
            return 1
        if protected_role_list is None or len(protected_role_list) == 0:
            bot_member: discord.Member = guild.get_member(self.bot.user.id)
            role_pos = sorted(bot_member.roles, key=lambda x: x.position)[-1].position - 1
        else:
            sorted_protected_role_list: List[discord.Role] = sorted(protected_role_list, key=lambda x: x.position)
            role_pos = sorted_protected_role_list[0].position
        if role_pos < 1:
            role_pos = 1
        return role_pos

    async def rearrange_custom_colour_role_positions(self, guild: discord.Guild):
        """
        Rearranges custom colour roles in a guild to ensure that they're still correctly positioned after updates to
        the guild's roles or the extension's protected roles and such.

        :param guild: Guild to rearrange roles in
        """
        role_pos = self.calculate_custom_colour_role_position(guild)
        roles: List[discord.Role] = [role for role in guild.roles if
                                     re.match(COLOUR_ROLE_NAMING, role.name)]
        for role in roles:
            await role.edit(position=role_pos)

    def get_guild_protected_colours(self, ctx: commands.Context) -> List[discord.Colour]:
        """
        Gets the list of protected roles' colours in the context's guild.

        :param discord.ext.commands.Context ctx: Context of the command
        :return: The list of the protected roles' colours
        :rtype: List[discord.Colour]
        """
        return ColourRole.get_role_colours(self.get_protected_roles(ctx.guild))

    @staticmethod
    def is_valid_colour_str(colour_str: str):
        """
        Checks if a string is a valid colour hex string value.

        :param colour_str: String to check
        :return: True if a valid colour hex string, false otherwise
        """
        if re.match("^([A-Fa-f0-9]{6})$", colour_str):
            return True
        return False

    @staticmethod
    def get_role_colours(roles: List[discord.Role]) -> List[discord.Colour]:
        """
        Gets the list of role colours from a list of roles.

        :param roles: Roles whose colours to get
        :return: The list of colours to return
        :rtype: List[discord.Colour]
        """
        role_colours = [role.colour for role in roles]
        role_colours.extend([discord.Colour.from_rgb(0, 0, 0), discord.Colour.from_rgb(54, 54, 54),
                             discord.Colour.from_rgb(255, 255, 255)])
        return role_colours

    @staticmethod
    def get_rgb_colour_distance(colour1: discord.Colour, colour2: discord.Colour) -> float:
        """
        Gets colour distance between two colours. Uses a low-cost algorithm sourced from
        https://www.compuphase.com/cmetric.htm to determine the distance between colours in a way that mimics human
        perception.

        :param colour1: Colour 1 for distance calculation
        :param colour2: Colour 2 for distance calculation
        :return: Distance between colours. Ranges from 0 to ~768.
        """
        r_diff = colour2.r - colour1.r
        r_sqr_diff = r_diff ** 2
        g_diff = colour2.g - colour1.g
        g_sqr_diff = g_diff ** 2
        b_diff = colour2.b - colour1.b
        b_sqr_diff = b_diff ** 2
        # Below from https://www.compuphase.com/cmetric.htm
        r_avg: float = (colour1.r + colour2.r) / 2
        b_fra = (255 - r_avg) / 256
        r_fra = r_avg / 256
        dist_sqr = ((2 + r_fra) * r_sqr_diff) + (4 * g_sqr_diff) + ((2 + b_fra) * b_sqr_diff)
        dist = math.sqrt(dist_sqr)
        return dist

    @staticmethod
    def is_valid_custom_colour(custom_colour: discord.Colour, protected_colours: List[discord.Colour]) -> Tuple[
        bool, Any]:
        """
        Checks if a given custom colour is a valid custom colour and not too close to any protected colours.

        :param custom_colour: Custom colour given
        :param protected_colours: List of protected colours in a guild
        :return: Tuple whose first element is True if valid, and False if invalid. If valid, the second element is None.
        Otherwise, the second element is the colour it ended up being too close to.
        """
        if not protected_colours:
            return True, None
        for protected_colour in protected_colours:
            colour_distance = ColourRole.get_rgb_colour_distance(custom_colour, protected_colour)
            KoalaBot.logger.info(
                f"Colour distance between {hex(custom_colour.value)} and {hex(protected_colour.value)} is {colour_distance}.")
            if colour_distance < 38.4:
                return False, protected_colour
        return True, None

    @staticmethod
    def role_already_exists(ctx: commands.Context, colour_str: str):
        """
        Checks if a custom colour role with a specific name already exists in the context's guild.

        :param ctx: Context of the command
        :param colour_str: Colour hex string to check
        :return: True if the role already exists, False otherwise.
        """
        role_name = f"KoalaBot[0x{colour_str}]"
        guild: discord.Guild = ctx.guild
        return role_name in [role.name for role in guild.roles]

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="listProtectedRoleColours",
                      aliases=["list_protected_role_colours", "listInvalidCustomColours", "listProtectedRoleColors",
                               "listInvalidCustomColors"])
    async def list_protected_role_colours(self, ctx: commands.Context):
        """
        Lists the protected roles, whose colours are protected from being imitated by a custom colour, in a
        guild. Requires admin permissions to use.

        :param ctx: Context of the command
        :return: Sends a message with the mentions of the roles that are protected in a guild
        """
        roles = self.get_protected_roles(ctx.guild)
        # print(roles)
        msg = "Roles whose colour is protected are:\r\n"
        for role in roles:
            msg += f"{role.mention}\n"
        await ctx.send(msg[:-1])

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="listCustomColourAllowedRoles",
                      aliases=["list_custom_colour_allowed_roles"])
    async def list_custom_colour_allowed_roles(self, ctx: commands.Context):
        """
        Lists the roles in a guild which are permitted to have their own custom colours. Requires admin
        permissions to use.

        :param ctx: Context of the command
        :return: Sends a message with the mentions of the roles that are protected in a guild.
        """
        roles = self.get_custom_colour_allowed_roles(ctx)
        # print(roles)
        msg = "Roles allowed to have a custom colour are:\r\n"
        for role in roles:
            msg += f"{role.mention}\n"
        await ctx.send(msg[:-1])

    def get_custom_colour_allowed_roles(self, ctx: commands.Context) -> List[discord.Role]:
        """
        Gets the list of roles in the context's guild that are allowed to have a custom colour.

        :param ctx: Context of the command
        :return: List of roles allowed to use the custom_colour command/have a custom colour
        """
        role_ids = self.cr_database_manager.get_colour_change_roles(ctx.guild.id)
        # print(role_ids)
        if not role_ids:
            return []
        guild: discord.Guild = ctx.guild
        roles = [guild.get_role(role_id) for role_id in role_ids]
        return roles

    def get_protected_roles(self, guild: discord.Guild) -> List[discord.Role]:
        """
        Gets the list of roles in the guild that are protected from custom colours.

        :param guild: Guild to check/access
        :return: List of roles which are protected
        """
        role_ids = self.cr_database_manager.get_protected_colour_roles(guild.id)
        # print(role_ids)
        if not role_ids:
            return []
        roles = [guild.get_role(role_id) for role_id in role_ids]
        return roles

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="addProtectedRoleColour",
                      aliases=["add_protected_role_colour", "addInvalidCustomColourRole", "addInvalidCustomColorRole",
                               "addProtectedRoleColor"])
    async def add_protected_role_colour(self, ctx: commands.Context, *, role_str: str):
        """
        Adds a role, via ID, mention or name, to the list of protected roles. Needs admin permissions to
        use.

        :param ctx: Context of the command
        :param role_str: The role to add (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.add_guild_protected_colour_role(ctx.guild.id, role.id)
            await ctx.send(f"Added {role.mention} to the list of roles whose colours are protected.")
            await self.rearrange_custom_colour_role_positions(ctx.guild)

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="removeProtectedRoleColour",
                      aliases=["remove_protected_role_colour", "removeProtectedRoleColor",
                               "removeInvalidCustomColourRole", "removeInvalidCustomColorRole"])
    async def remove_protected_role_colour(self, ctx: commands.Context, *, role_str: str):
        """
        Removes a role, via ID, mention or name, from the list of protected roles. Needs admin permissions
        to use.

        :param ctx: Context of the command
        :param role_str: The role to remove (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.remove_guild_protected_colour_role(ctx.guild.id, role.id)
            await ctx.send(f"Removed {role.mention} from the list of roles whose colours are protected.")
            await self.rearrange_custom_colour_role_positions(ctx.guild)

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="addCustomColourAllowedRole",
                      aliases=["add_custom_colour_allowed_role", "addCustomColorAllowedRole"])
    async def add_custom_colour_allowed_role(self, ctx: commands.Context, *, role_str: str):
        """
        Adds a role, via ID, mention or name, to the list of roles allowed to have a custom colour. Needs
        admin permissions to use.

        :param ctx: Context of the command
        :param role_str: The role to add (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            self.cr_database_manager.add_colour_change_role_perms(ctx.guild.id, role.id)
            await ctx.send(f"Added {role.mention} to the list of roles allowed to have a custom colour.")

    @commands.check(KoalaBot.is_admin)
    @commands.check(colour_is_enabled)
    @commands.command(name="removeCustomColourAllowedRole",
                      aliases=["remove_custom_colour_allowed_role", "removeCustomColorAllowedRole"])
    async def remove_custom_colour_allowed_role(self, ctx: commands.Context, *, role_str: str):
        """
        Removes a role, via ID, mention or name, from the list of roles allowed to have a custom colour.
        Needs admin permissions to use.

        :param ctx: Context of the command
        :param role_str: The role to remove (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        if not role:
            await ctx.send("Please specify a single valid role's mention, ID or name.")
        else:
            members: List[discord.Member] = role.members
            await self.prune_members_old_colour_roles(members)
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
            """INSERT INTO GuildColourChangePermissions (guild_id, role_id) VALUES (?, ?);""", args=[guild_id, role_id])

    def remove_colour_change_role_perms(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            """DELETE FROM GuildColourChangePermissions WHERE guild_id = ? AND role_id = ?;""", args=[guild_id, role_id])

    def add_guild_protected_colour_role(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            """INSERT INTO GuildInvalidCustomColourRoles (guild_id, role_id) VALUES (?, ?);""", args=[guild_id, role_id])

    def remove_guild_protected_colour_role(self, guild_id, role_id):
        self.database_manager.db_execute_commit(
            """DELETE FROM GuildInvalidCustomColourRoles WHERE guild_id = ? AND role_id = ?;""", args=[guild_id, role_id])

    def get_protected_colour_roles(self, guild_id) -> List[int]:
        rows = self.database_manager.db_execute_select(
            """SELECT * from GuildInvalidCustomColourRoles WHERE guild_id = ?;""", args=[guild_id])
        if rows is None:
            return None
        return [row[1] for row in rows]

    def get_colour_change_roles(self, guild_id) -> List[int]:
        rows = self.database_manager.db_execute_select(
            """SELECT * from GuildColourChangePermissions WHERE guild_id = ?;""", args=[guild_id])
        if rows is None:
            return None
        return [row[1] for row in rows]


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(ColourRole(bot))
    print("ColourRole is ready.")
