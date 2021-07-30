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
            guild_id text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (guild_id, role_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            )"""
        ignore_list = """CREATE TABLE IF NOT EXISTS exempt_users (
            guild_id text NOT NULL,
            user_id text NOT NULL,
            PRIMARY KEY (guild_id, user_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )
        """
        guest_role = """CREATE TABLE IF NOT EXISTS guest_roles (
            guild_id text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (guild_id, role_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )
        """
        roles_to_remove = """CREATE TABLE IF NOT EXISTS roles_to_remove (
            guild_id text NOT NULL
            role_id text NOT NULL
            PRIMARY KEY (guild_id, role_id)
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )
        """
        self.DBManager.db_execute_commit(roles_to_remove)
        self.DBManager.db_execute_commit(required_roles)
        self.DBManager.db_execute_commit(ignore_list)
        self.DBManager.db_execute_commit(guest_role)

    @commands.Bot.event
    async def on_ready(self):
        all_guilds_and_guest_roles = self.get_all_guilds_and_guest_roles()
        for (guild_id, role_id) in all_guilds_and_guest_roles:
            guild = self.bot.get_guild(int(guild_id))
            role = guild.get_role(int(role_id))
            for user in [u for u in guild.users if self.has_required_role(guild_id, u)]:
                self.remove_roles(guild_id, user)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        guest_role = self.DBManager.db_execute_select("""
        SELECT role_id FROM  guest_roles WHERE guild_id = ?
        """, guild_id)
        if guest_role:
            role = discord.utils.get(member.guild.roles, id=int(guest_role[0][0]))
            await member.add_roles(role)
        else:
            pass


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
        guild_id = ctx.guild.id
        role_id = role.id
        self.add_required_role_to_db(role_id, guild_id)

    @auto_role.command(name="removeRequiredRole", aliases=["remove_required_role"])
    async def remove_required_role(self, ctx: commands.Context, role: discord.Role):
        """
        Removes a role from the required_roles database.
        :param ctx: The discord context of the command.
        :param role: The role to be made required by all users.
        """
        guild_id = ctx.guild.id
        role_id = role.id
        self.remove_required_role_from_db(role_id, guild_id)

    @auto_role.command(name="setGuestRole", aliases=["set_guest_role"])
    async def set_required_role(self, ctx : commands.Context, role : discord.Role):
        """
        Sets the guest role for the server.
        :param ctx: The discord context of the command:
        :param role: The role to be made the guest role.
        """
        guild_id = ctx.guild.id
        role_id = role.id
        self.add_required_role_to_db(guild_id, role_id)


    @auto_role.command(name="addExemptUser", aliases=["add_exempt_user"])
    async def add_exempt_user(self, ctx: commands.Context, user: discord.Member):
        """
        Makes a user exempt from the auto role extension.
        :param ctx: The discord context of the command.
        :param user: The user to be made exempt.
        """
        guild_id = ctx.guild.id
        user_id = user.id
        self.add_exempt_user_to_db(self, guild_id, user_id)

    @auto_role.command(name="removeExemptUser", aliases=["remove_exempt_user"])
    async def remove_exempt_user(self, ctx: commands.Context, user: discord.Member):
        """
        Stops a user exempt from the auto role extension.
        :param ctx: The discord context of the command.
        :param user: The user to be made subject to auto role.
        """
        guild_id = ctx.guild.id
        user_id = user.id
        self.remove_exempt_user_to_db(self, guild_id, user_id)

    @auto_role.command(name="addExemptRole", aliases=["add_exempt_role"])
    async def add_exempt_role(self, ctx: commands.Contextm, role: discord.Role):
        guild_id = ctx.guild.id
        for member in role.members:
            self.add_exempt_user_to_db(guild_id, member.id)

    @auto_role.command(name="removeExemptRole", aliases=["remove_exempt_role"])
    async def remove_exempt_role(self, ctx: commands.Contextm, role: discord.Role):
        guild_id = ctx.guild.id
        for member in role.members:
            self.remove_exempt_user_to_db(guild_id, member.id)

    def remove_required_role_from_db(self, role_id: str, guild_id: str):
        """
        Makes a role un necessary for users to have in a guild.
        :param role_id: The un necessary role's id.
        :param guild_id: The guild to remove role from the required role list.
        """
        self.DBManager.execute_commit("""
        DELETE FROM required_roles WHERE role_id = ? AND guild_id = ?
        """, role_id, guild_id)

    def add_required_role_to_db(self, role_id: str, guild_id: str):
        """
        Sets the required role that all users in a guild must have.
        :param role_id: The required role's id.
        :param guild_id: The guild to make this role required.
        """
        self.DBManager.db_execute_commit("""
        INSERT INTO required_roles (guild_id, role_id)
        VALUES (?, ?)
        """, guild_id, role_id)

    def add_guest_role_to_db(self, guild_id, role_id):
        """
        Adds the specified role to the guest_role db
        :param guild_id: = The id of the server to set the guest role
        :param role_id: = The id of the role to be made the guest role
        """
        self.DBManager.db.execute_commit("""
        INSERT INTO guest_roles (guild_id, role_id)
        VALUES (?, ?)
        """, guild_id, role_id)

    def add_exempt_user_to_db(self, guild_id: str, user_id: str):
        """
        Adds the specified user to the exempt_user database.
        :param guild_id: The guild the user is exempt from auto role.
        :param user_id: The user to be made exempt from auto role.
        """
        self.DBManager.execute_commit("""
        INSERT INTO exempt_users (guild_id, user_id) VALUES (?, ?)
        """, guild_id, user_id)

    def remove_exempt_user_to_db(self, guild_id: str, user_id: str):
        """
        Removes the specified user from the exempt_user database.
        :param guild_id: The guild the user is liable to the auto role extension.
        :param user_id: The user to be made liable to the auto role extension.
        """
        self.DBManager.execute_commit("""
        DELETE FROM exempt_users WHERE guild_id = ? AND user_id = ?
        """, guild_id, user_id)

    def remove_required_role(self, role_id: str, guild_id: str):
        """
        Makes a role un necessary for users to have in a guild.
        :param role_id: The un necessary role's id.Member
        :param guild_id: The guild to remove role from the required role list.
        """
        self.DBManager.execute_commit("""
        DELETE FROM required_roles WHERE role_id = ? AND guild_id = ?
        """, role_id, guild_id)

    def ignore_user(self, user_id: str, guild_id: str):
        """
        Check to see if the user is in the ignore_auto_role list.
        :params user: The discord user to check for.
        :return: True if user is in the ignore_auto_role list, false otherwise
        """
        if self.DBManager.db_execute_select("""SELECT user_id FROM exempt_users WHERE guild_id = ? AND user_id = ?""", guild_id, user_id):
            return True
        return False

    def get_all_guilds_and_guest_roles(self):
        """
        Gets all guilds AutoRole is enabled on
        """
        all_guilds_and_roles = self.DBManager.db_execute_select("""SELECT guild_id, role_id FROM guest_roles
        """)
        return all_guilds_and_roles

    async def remove_roles(self, guild_id : int, user : discord.Member):
        """
        Removes all the specified roles from the user.
        :param guild: The server that specifies the roles to be removed.
        :param user: The user to remove roles from.
        """
        roles_to_remove = self.DBManager.db_execute_select("""SELECT role_id FROM roles_to_remove WHERE guild_id = ?
        """, guild_id)
        for (role_id,) in roles_to_remove:
            role = self.bot.get_role(int(role_id))
            await user.remove_roles(role_id)

    def has_required_role(self, guild_id : int, user : discord.Member):
        """
        Checks to see if a user has any of a server's required roles.
        :param user: The user to check.
        :guild_id: The server id the user is a part of.
        :return: True if the user has any of the guilds required roles, false otherwise.
        """
        required_roles = self.DBManager.db_execute_select("""SELECT role_id FROM required_roles WHERE guild_id = ?""", str(guild_id))
        for (role_id,) in required_roles:
            role = bot.get_role(int(role_id))
            if role in user.roles:
                return True
        return False


def setup(bot):
    """
    Adds the cog to the bot
    :param bot: The bot the Auto Role cog is being added to
    """
    bot.add_cog(AutoRole(bot))
    print("Auto Role is ready.")
