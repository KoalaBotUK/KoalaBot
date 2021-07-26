#!/usr/bin/env python

"""
Koala Bot Advanced Verification cog with API functions
Commented using reStructuredText (reST)
Created by: Suhail Merali & Oluwaponmile Femi-Sunmaila
"""

# Built-in/Generic Imports
import aiohttp
from aiohttp import web
import asyncio
import time
from aiohttp.web_exceptions import HTTPBadRequest, HTTPForbidden

# Libs
import discord
from discord.ext import commands


# Own modules
import KoalaBot


app = web.Application()
routes = web.RouteTableDef()




class AdvancedVerification(commands.Cog, name="AdvancedVerify",
    description = ""):

    def __init__(self, bot, db_manager=None):
        self.bot = bot
        if not db_manager:
            self.DBManager = KoalaBot.database_manager
            self.DBManager.insert_extension("AdvancedVerify", 0, True, True)
        else:
            self.DBManager = db_manager

        self.add_routes()

        asyncio.create_task(self.start_server())
    
    def advanced_verify_is_enabled(self, s_id: str):
        try:
            return self.DBManager.extension_enabled(s_id, "Verify") and self.DBManager.extension_enabled(s_id, "AdvancedVerify")
        except:
            return

    def set_up_tables(self):
        """
        Creates tables necessary for the advanced verification cog to function
        :return:
        """
        adv_table = """
        CREATE TABLE IF NOT EXISTS advanced_verification (
        s_id integer NOT NULL,
        r_id integer NOT NULL,
        email text NOT NULL,
        PRIMARY KEY (s_id, r_id, email)
        FOREIGN KEY (s_id) REFERENCES GuildExtensions (guild_id)
        )"""

        self.DBManager.db_execute_commit(adv_table)


    def cog_unload(self):
        asyncio.create_task(self.stop_server())


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Assigns necessary roles to users upon joining a server
        :param member: the member object who just joined a server
        :return:
        """
        linked_emails = self.DBManager.db_execute_select("SELECT email FROM verified_emails WHERE u_id = ?", (member.id))

        for (email,) in linked_emails:
            potential_roles = self.DBManager.db_execute_select("SELECT r_id FROM advanced_verification WHERE email = ? AND s_id = ?", (email, member.guild.id))
            for (role_id,) in potential_roles:
                blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                               (role_id, member.id))
                if not blacklisted:
                    await member.add_roles(member.guild.get_role(role_id))


    
    def raise_error(self, error_msg, status=400):
        data = {"error": error_msg}
        return web.json_response(data, status=status)

    async def check_and_give_role(self, guild: discord.Guild, role: discord.Role, email: str):
        potential_users = self.DBManager.db_execute_select("SELECT u_id from verified_emails WHERE email = ?", (email,))
        if potential_users:
            u_id = potential_users[0][0]
            try:
                member = guild.get_member(u_id)
                if not member:
                    member = await guild.fetch_member(u_id)
            except discord.NotFound:
                return
            else:
                await member.add_roles(role)

    def add_to_database(self, s_id: int, r_id: int, email: str):
        self.DBManager.db_execute_commit("INSERT INTO advanced_verification (s_id, r_id, email) VALUES (?, ?, ?)", (s_id, r_id, email))


    def add_routes(self):
        #TODO - rate limiting
        @routes.post("/adv_verify")
        async def advanced_verify(request: web.Request):
            if await self.check_verification(request.headers.get("authorization")):
                raise HTTPForbidden() 

            data = await request.json()

            if "client-id" not in data or "role-id" not in data or "user-email" not in data:
                return self.raise_error("Data missing fields")

            guild_id = data["client-id"]
            if not guild_id or str(guild_id).isdigit():
                return self.raise_error("Server ID is not a number")
            guild : discord.Guild = self.bot.get_guild(int(guild_id))
            if not guild:
                return self.raise_error(f"Server with ID {guild_id} does not exist or KoalaBot is not in server")           
            if not self.advanced_verify_is_enabled(guild.id):
                return self.raise_error(f"Server with ID {guild_id} does not have the Advanced Verify extension enabled.")

            role_id = data["role-id"]
            if not role_id or str(role_id).isdigit():
                return self.raise_error("Role ID is not a number")
            role: discord.Role = guild.get_role(int(role_id))
            if not role:
                return self.raise_error(f"Server does not have role with ID {role_id}")
            

            emails = data["user-email"]
            if isinstance(emails, str):
                emails = [emails]

            for email in emails:
                await self.check_and_give_role(guild.id, role.id, email)
                self.add_to_database(guild.id, role.id, email)
                



    async def check_verification(self, auth_token):
        """
        Checks if the request has a valid auth token
        :param auth_token: the authorization token of the request
        """
        return True #TODO - check API Tokens

    async def start_server(self):
        """
        Starts up the web server that hosts the API
        """
        await self.bot.wait_until_ready()
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, "0.0.0.0", 8080)
        await self.site.start()

    async def stop_server(self):
        """
        Shuts down the webserver hosting the API
        """
        await self.site.stop()


def setup(bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(AdvancedVerification(bot))