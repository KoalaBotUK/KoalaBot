#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

Author: Suhail Merali & Oluwaponmile Femi-Sunmaila
Commented using reStructuredText (reST)
"""

# Libs
import discord
from discord.ext import commands



def auto_role_is_enabled(self, s_id: str):
    try:
        return KoalaBot.database_manager.extension_enabled(s_id, "AutoRole") 
    except:
        return


class AutoRole(commands.Cog, description = ""):

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
        ignore_list = """CREATE TABLE IF NOT EXISTS ignore_users (
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
    async def auto_role(self, ctx : commands.Context):
        await ctx.send_help("autoRole")

    @auto_role.command(name="addRequiredRole", aliases = ["add_required_role"])
    async def add_required_role(self, ctx : commands.Context, role : discord.Role):
        guild_id = ctx.guild
        role_id = role.id
        self.set_required_role(role_id, guild_id)
        



    def set_required_role(self, role_id : int, guild_id : int):
        """
        Sets the required role that all users in a guild must have
        :param role: The required role
        """
        pass
    
    def ignore_user(self, user : discord.Member):
        """
        Check to see if the user is in the ignore_auto_role list.
        :params user: The discord user to check for.
        :return: True if user is in the ignore_auto_role list, false otherwise
        """
        pass

    

def setup(bot):
    bot.add_cog(AutoRole(bot))
    print("Auto Role is ready.")

