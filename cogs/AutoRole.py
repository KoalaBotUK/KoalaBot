#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

Author: Suhail Merali & Oluwaponmile Femi-Sunmaila
Commented using reStructuredText (reST)
"""

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot


def auto_role_is_enabled(self, s_id: str):
    """
    Determines whether the AutoRole extension is enabled in a server
    :param s_id: The id of the server
    """
    try:
        return KoalaBot.database_manager.extension_enabled(s_id, "AutoRole")
    except:
        return


class AutoRole(commands.Cog, description=""):

    def __init__(self, bot: commands.Bot, db_manager=None):
        self.bot = bot
        if not db_manager:
            self.DBManager = KoalaBot.database_manager
            self.DBManager.insert_extension("AutoRole", 0, True, True)
        else:
            self.DBManager = db_manager

    def set_up_tables(self):
        """
        Creates tables necessary for the auto role cog to function.
        """
        required_roles = """CREATE TABLE IF NOT EXISTS required_roles (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            )"""
        ignore_list = """CREATE TABLE IF NOT EXISTS exempt_users (
            guild_id integer NOT NULL,
            user_id integer NOT NULL,
            PRIMARY KEY (guild_id, user_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )
        """
        self.DBManager.db_execute_commit(required_roles)
        self.DBManager.db_execute_commit(ignore_list)

    @commands.group(name="autoRole", aliases=["auto_role"], invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.check(auto_role_is_enabled)
    async def auto_role(self, ctx: commands.Context):
        await ctx.send_help("autoRole")

    @auto_role.command(name="addRequiredRole", aliases=["add_required_role"])
    async def add_required_role(self, ctx: commands.Context, role: discord.Role):
        """
        Adds a role that all users must have.
        :param ctx: The discord context of the command.
        :param role: The role to be made required by all users.
        """
        guild_id = ctx.guild
        role_id = role.id
        self.set_required_role(role_id, guild_id)

    @auto_role.command(name="removeRequiredRole", aliases=["remove_required_role"])
    async def add_required_role(self, ctx: commands.Context, role: discord.Role):
        """
        Removes a role from the required_roles database.
        :param ctx: The discord context of the command.
        :param role: The role to be made required by all users.
        """
        guild_id = ctx.guild
        role_id = role.id
        self.remove_required_role(role_id, guild_id)

    @auto_role.command(name="addExemptUser", aliases=["add_exempt_user"])
    async def add_exempt_user(self, ctx: commands.Context, user: discord.Member):
        """
        Makes a user exempt from the auto role extension.
        :param ctx: The discord context of the command.
        :param user: The user to be made exempt.
        """
        guild_id = ctx.guild
        user_id = user.id
        self.add_exempt_user_to_db(self, guild_id, user_id)

    @auto_role.command(name="removeExemptUser", aliases=["remove_exempt_user"])
    async def remove_exempt_user(self, ctx: commands.Context, user: discord.Member):
        """
        Stops a user exempt from the auto role extension.
        :param ctx: The discord context of the command.
        :param user: The user to be made subject to auto role.
        """
        guild_id = ctx.guild
        user_id = user.id
        self.remove_exempt_user_to_db(self, guild_id, user_id)

    def remove_required_role(self, role_id: int, guild_id: int):
        """
        Makes a role un necessary for users to have in a guild.
        :param role_id: The un necessary role's id.
        :param guild_id: The guild to remove role from the required role list.
        """
        try:
            self.DBManager.execute_commit("""
            DELETE FROM required_roles WHERE role_id = ? AND guild_id = ?
            """, role_id, guild_id)
        except:
            pass

    def set_required_role(self, role_id: int, guild_id: int):
        """
        Sets the required role that all users in a guild must have.
        :param role_id: The required role's id.
        :param guild_id: The guild to make this role required.
        """
        try:
            self.DBManager.db_execute_commit("""
            INSERT INTO required_roles (guild_id, role_id)
            VALUES (?, ?)
            """, guild_id, role_id)
        except:
            pass

    def add_exempt_user_to_db(self, guild_id: int, user_id: int):
        """
        Adds the specified user to the exempt_user database.
        :param guild_id: The guild the user is exempt from auto role.
        :param user_id: The user to be made exempt from auto role.
        """
        try:
            self.DBManager.execute_commit("""
            INSERT INTO exempt_users (guild_id, user_id) VALUES (?, ?)
            """, guild_id, user_id)
        except:
            pass

    def remove_exempt_user_to_db(self, guild_id: int, user_id: int):
        """
        Removes the specified user from the exempt_user database.
        :param guild_id: The guild the user is liable to the auto role extension.
        :param user_id: The user to be made liable to the auto role extension.
        """
        try:
            self.DBManager.execute_commit("""
            DELETE FROM exempt_users WHERE guild_id = ? AND user_id = ?
            """, guild_id, user_id)
        except:
            pass

    def ignore_user(self, user: discord.Member):
        """
        Check to see if the user is in the ignore_auto_role list.
        :params user: The discord user to check for.
        :return: True if user is in the ignore_auto_role list, false otherwise
        """
        pass


def setup(bot):
    """
    Adds the cog to the bot
    :param bot: The bot the Auto Role cog is being added to
    """
    bot.add_cog(AutoRole(bot))
    print("Auto Role is ready.")
