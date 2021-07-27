#!/usr/bin/env python

"""
Koala Bot Advanced Verification cog with API functions
Commented using reStructuredText (reST)
Created by: Suhail Merali & Oluwaponmile Femi-Sunmaila
"""

# Built-in/Generic Imports
import os
from typing import Any, Dict, Optional
from aiohttp import web
from aiohttp.web_exceptions import HTTPForbidden, HTTPNoContent, HTTPTooManyRequests, HTTPUnauthorized
import asyncio
import time, datetime
from dotenv import load_dotenv

# Libs
import discord
from discord.ext import commands
import jwt


# Own modules
import KoalaBot


app = web.Application()
routes = web.RouteTableDef()

load_dotenv()
TOKEN_GENERATION_KEY = os.environ.get("TOKEN_GENERATION_KEY")


RATELIMIT = 100
RESET_EVERY = 60


def advanced_verify_is_enabled(self, s_id: str):
    try:
        return KoalaBot.database_manager.extension_enabled(s_id, "Verify") and KoalaBot.database_manager.extension_enabled(s_id, "AdvancedVerify")
    except:
        return

def httpdate(dt):
    """Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    The supplied date must be in UTC.

    """
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
            "Oct", "Nov", "Dec"][dt.month - 1]
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
        dt.year, dt.hour, dt.minute, dt.second)

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
        self.set_up_tables()

        self.server_ratelimits = {}

        asyncio.create_task(self.start_server())

    def set_up_tables(self):
        """
        Creates tables necessary for the advanced verification cog to function
        """
        adv_table = """
        CREATE TABLE IF NOT EXISTS advanced_verification (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        email text NOT NULL,
        PRIMARY KEY (guild_id, role_id, email)
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )"""

        tokens = """
        CREATE TABLE IF NOT EXISTS verification_tokens (
        token text NOT NULL,
        PRIMARY KEY (token)
        """

        self.DBManager.db_execute_commit(adv_table)
        self.DBManager.db_execute_commit(tokens)


    def cog_unload(self):
        """
        Stops the web server once the cog is unloaded
        """
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
            potential_roles = self.DBManager.db_execute_select("SELECT role_id FROM advanced_verification WHERE email = ? AND guild_id = ?", (email, member.guild.id))
            for (role_id,) in potential_roles:
                blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                               (role_id, member.id))
                if not blacklisted:
                    await member.add_roles(member.guild.get_role(role_id))


    @staticmethod
    def raise_error(error_msg: str, status: int = 400, headers: Dict[str, Any] = None) -> web.Request:
        """
        Creates an error response.
        :param error_msg: information as to what caused the error.
        :param status: The relevant status code.
        :param headers: response headers.
        :return: a web response with error information.
        """
        data = {"error": error_msg}
        return web.json_response(data, status=status, headers=headers)

    async def check_and_give_role(self, guild: discord.Guild, role: discord.Role, email: str):
        """
        Assigns the specified user a role.
        :param guild: The server of the user being assigned the role.
        :param role: The role to be given.
        :param email: The email of the user to be assigned the role.
        """
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
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    return

    def add_to_database(self, s_id: int, r_id: int, email: str):
        """
        Adds an entry to The advanced_verification table.
        :param s_id: The server id of the user.
        :param r_id: The role's id.
        :param email: The user's email.
        """
        self.DBManager.db_execute_commit("INSERT INTO advanced_verification (guild_id, role_id, email) VALUES (?, ?, ?)", (s_id, r_id, email))

    def ratelimit(self, guild_id: int) -> Dict[str, Any]:
        """
        Updates the amount of times a server has made a request in the last minute.
        :param guild_id: The server making the request.
        :return: The remaining amount of times the server can make a request until the next minute.
        """
        if guild_id not in self.server_ratelimits or self.server_ratelimits[guild_id]["reset_after"] > time.time():
            self.server_ratelimits[guild_id] = {
                "remaining": RATELIMIT - 1,
                "reset_after": round(time.time() + RESET_EVERY)
            }
        else:
            self.server_ratelimits[guild_id]["remaining"] -= 1
        
        return self.get_headers(self.server_ratelimits[guild_id])
    
    @staticmethod
    def get_headers(data: Dict[str, int]) -> Dict[str, Any]:
        """
        Adds headers to the request relating to ratelimiting.
        :param data: Ratelimiting information.
        """
        headers = {
            "X-RateLimit-Limit": RATELIMIT,
            "X-RateLimit-Remaining": data["remaining"],
            "X-RateLimit-Reset": data["reset_after"] - time.time(),
            "Retry-After": httpdate(time.gmtime(data["reset_after"]))
        }

        return headers

    def check_ratelimit(self, guild_id: int) -> bool:
        """
        Checks to see if a server is above the ratelimit.
        :params guild_id: The server to check for ratelimiting.
        :return: True if The server is allowed to make at least 1 more request, False otherwise.
        """
        return guild_id not in self.server_ratelimits or self.server_ratelimits[guild_id]["remaining"] > 0
    
        
    def add_routes(self):
        @routes.post("/adv_verify")
        async def advanced_verify(request: web.Request) -> web.Response:
            """
            Handles verification requests
            :param request: The web request.
            :return: Error 429 Too Many Requests or Error 400 Bad Request.
            :raise: 401 Unauthorized, 403 Forbidden or 204 No Content.
            """

            valid_guild_id = self.check_verification(request.headers.get("Authorization"))

            if not valid_guild_id:
                raise HTTPUnauthorized() 

            if not self.check_ratelimit(valid_guild_id):
                return self.raise_error(f"Ratelimit Reached For Server {valid_guild_id}", 429, self.get_headers(self.server_ratelimits[valid_guild_id]))

            data = await request.json()

            if "client-id" not in data or "role-id" not in data or "user-email" not in data:
                return self.raise_error("Data missing fields")

            guild_id = data["client-id"]
            if not guild_id or str(guild_id).isdigit():
                return self.raise_error("Server ID is not a number")
            guild : discord.Guild = self.bot.get_guild(int(guild_id))
            if not guild:
                return self.raise_error(f"Server with ID {guild_id} does not exist or KoalaBot is not in server")
            if str(guild.id) != str(valid_guild_id):
                raise HTTPForbidden()
            if not advanced_verify_is_enabled(guild.id):
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

            headers = self.ratelimit(valid_guild_id)

            raise HTTPNoContent(headers=headers)
                

    def check_verification(self, auth_token: str) -> Optional[int]:
        """
        Checks if the request has a valid auth token.
        :param auth_token: The authorization token of the request.
        """
        PREFIX = "Bearer "

        if not auth_token.startswith(PREFIX):
            return None
        
        auth_token = auth_token[len(PREFIX):]

        try:
            decoded = jwt.decode(auth_token, TOKEN_GENERATION_KEY, algorithms="HS256")
        except jwt.DecodeError:
            return None
        else:

            if self.DBManager.db_execute_select("SELECT * FROM verification_tokens WHERE token = ?", auth_token):
                return decoded.get("guild_id")
            return None
    
    def create_token(self, user_id: int, guild_id: int) -> str:
        """
        Creates a token based on ids.
        :param user_id: The ID of the Discord User.
        :param guild_id: The ID of the Server.
        """

        data = {
            "user_id": user_id,
            "guild_id": guild_id,
            "iat": datetime.datetime.utcnow()
        }

        encoded = jwt.encode(data, TOKEN_GENERATION_KEY, algorithm="HS256")

        return encoded

    def invalidate_old_tokens(self, user_id: int, guild_id: int):
        """
        Removes any previous tokens formed from the user and server.
        :param user_id: The user ID that makes up the old token.
        :param guild_id: The server ID that makes up the old token.
        """
        for (token,) in self.DBManager.db_execute_select("SELECT token FROM verification_tokens"):
            try:
                decoded = jwt.decode(token, TOKEN_GENERATION_KEY, algorithms="HS256")
                if decoded["user_id"] == user_id and decoded["guild_id"] == guild_id:
                    self.invalidate_token(token)
            except jwt.DecodeError:
                self.invalidate_token(token)
            except KeyError:
                self.invalidate_token(token)
    
    def get_token(self, user_id: int, guild_id: int) -> Optional[str]:
        """
        Gets a token from the verification_tokens table.
        :param user_id: The user ID making up the requested token.
        :param guild_id: The server ID making up the requested token.
        """
        for (token,) in self.DBManager.db_execute_select("SELECT token FROM verification_tokens"):
            try:
                decoded = jwt.decode(token, TOKEN_GENERATION_KEY, algorithms="HS256")
                if decoded["user_id"] == user_id and decoded["guild_id"] == guild_id:
                    return token
            except jwt.DecodeError:
                self.invalidate_token(token)
            except KeyError:
                self.invalidate_token(token)
                    

    def save_token(self, token: str):
        """
        Saves a new token to the verification_tokens table.
        :param toke: Token to be saved.
        """
        self.DBManager.db_execute_commit("INSERT INTO verification_tokens (token) VALUES (?)", token)

    def invalidate_token(self, token: str):
        """
        Removes an old token from the verification_tokens table.
        :param token: The token to be removed.
        """
        self.DBManager.db_execute_commit("DELETE FROM verification_tokens WHERE token = ?", token)

    async def start_server(self):
        """
        Starts up the web server that hosts the API.
        """
        await self.bot.wait_until_ready()
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, "0.0.0.0", 8080)
        await self.site.start()

    async def stop_server(self):
        """
        Shuts down the webserver hosting the API.
        """
        await self.site.stop()



    @commands.group(name="advancedVerify", aliases=["advVerify", "advanced_verify"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.check(advanced_verify_is_enabled)
    async def advanced_verification(self, ctx: commands.Context):
        await ctx.send_help("advancedVerify")

    @advanced_verification.command(name="generateToken", aliases=["generate", "genToken", "gen_token", "generate_token"])
    async def generate_token_command(self, ctx: commands.Context):
        """
        Generates a new server specific token for a the user, automatically invalidating old ones.
        :param ctx: The context of the message
        """
        self.invalidate_old_tokens(ctx.author.id, ctx.guild.id)
        token = self.create_token(ctx.author.id, ctx.guild.id)
        await ctx.author.send(f"Your API token for {ctx.guild.name} is:\n{token}\**nDO NOT** share this token with anyone. Any old tokens have been revoked.")
        self.save_token(token)
    
    @advanced_verification.command(name="getToken", aliases=["get_token", "get"])
    async def get_token_command(self, ctx: commands.Context): 
        """
        Gets an already existing token for the user for that server, notifying them if one doesn't exist
        """
        token = self.get_token(ctx.author.id, ctx.guild.id)
        if not token:
            await ctx.send(f"You have not generated a token before. Use {ctx.prefix}advancedVerify generateToken` to generate one.")
            return
        await ctx.author.send(f"Your API token for {ctx.guild.name} is:\n\n{token}\n\n**nDO NOT** share this token with anyone.")
    
    @advanced_verification.command(name="invalidateToken", aliases=["invalidate", "invalidate_token"])
    async def invalidate_token_command(self, ctx: commands.Context, token: str):
        self.invalidate_token(token)
        await ctx.send("Token invalidated", delete_after=5.0)
        

def setup(bot):
    """
    Load this cog to the KoalaBot.
    :param bot: The bot client for KoalaBot
    """
    if not TOKEN_GENERATION_KEY:
        print("Advanced Verification not started. Key not found in environment")
        KoalaBot.database_manager.insert_extension("AdvancedVerify", 0, False, False)
    else:
        bot.add_cog(AdvancedVerification(bot))
        print("Advanced Verification is ready.")