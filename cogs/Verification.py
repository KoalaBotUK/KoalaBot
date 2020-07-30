#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
import random
import string


# Libs
import validators
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager


# Constants

# Variables

def is_dm_channel(ctx):
    return ctx.channel.id == ctx.author.dm_channel.id


class Verification(commands.Cog):
    """
        A discord.py cog with general commands useful to managers of the bot and servers
    """

    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        self._last_member = None
        self.started = False
        self.DBmanager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)
        self.DBmanager.db_execute_commit("CREATE TABLE IF NOT EXISTS server_info (guild_id, role_id, domain)")
        self.DBmanager.db_execute_commit(
            "CREATE TABLE IF NOT EXISTS verified_users (guild_id, user_id, domain, token, verified, role_assigned)")
        self.loop = self.bot.loop.create_task(self.verify_user_loop())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Function triggers on user joining a server
        :param member: the user who joined
        """
        exists = self.DBmanager.db_execute_select("SELECT * FROM server_info WHERE guild_id=?",
                                                  args=(member.guild.id,))

        # sends a dm to a user if the server they are joining has any verification enabled
        if exists:
            await member.send(
                "Hi, I see you've logged in. Please verify with a student email address with `k!verify <email>`")

    @commands.command(name="enable_verification")
    async def enable(self, ctx, domain, role):
        """
        Enables verification for a role
        :param ctx: context of the message
        :param domain: domain to be verified
        :param role: role to be verified
        """
        if not role:
            await ctx.send("Please provide a role to give to verified users")
            return

        if not validators.domain(domain):
            await ctx.send("Please provide a valid domain")
            return

        role_id = role[3:-1]
        exists = self.DBmanager.db_execute_select("SELECT * FROM server_info WHERE guild_id=? AND role_id=?",
                                                  args=(ctx.guild.id, role_id))
        if exists:
            await ctx.send("Verification is already enabled for that role")
            return

        self.DBmanager.db_execute_commit("INSERT INTO server_info VALUES (?, ?, ?)",
                                         args=(ctx.guild.id, role_id, domain))
        await ctx.send(f"Verification enabled for <@&{role_id}> for emails with the domain {domain}")

    @commands.command(name="disable_verification")
    async def disable(self, ctx, domain, role):
        """
        Disables verification for a specific role
        :param ctx: context of the message
        :param domain: domain to stop verifying
        :param role: role to stop verifying
        """
        role_id = role[3:-1]
        self.DBmanager.db_execute_commit("DELETE FROM server_info WHERE domain=? AND role_id=? AND guild_id=?",
                                         args=(domain, role_id, ctx.guild.id))
        await ctx.send(f"Emails with {domain} no longer give {role}")

    @commands.check(is_dm_channel)
    @commands.command(name="verify")
    async def verify(self, ctx, guild_id, email):
        """
        Starts the verification process for a user
        :param ctx: context for the message sent
        :param guild_id: guild they are verifying for
        :param email: the user's email address
        """
        domain = email.split("@", 1)[1]
        exists = self.DBmanager.db_execute_select("SELECT * FROM server_info WHERE guild_id=? AND domain=?",
                                                  args=(ctx.guild.id, domain))
        if not exists:
            await ctx.send("That is not a domain that server allows")
            return

        member = self.bot.get_guild(guild_id).get_member(ctx.author.id)
        if not member:
            await ctx.send("You are not in that server")
            return

        already_verified = self.DBmanager.db_execute_select("SELECT * FROM verified_users WHERE user_id=? AND domain=?",
                                                            args=(ctx.author.id, domain))
        if already_verified:
            await ctx.send("You are already verified for that role")
            return

        verification_code = ''.join(random.choice(string.ascii_letters) for i in range(8))
        self.DBmanager.db_execute_commit("INSERT INTO verified_users VALUES (?, ?, ?, ?, ?, ?)",
                                         args=(ctx.guild.id, ctx.author.id, domain, verification_code, 0, 0))

        # send email code, link something like https://koalabot.uk/verify?code={verification_code}"

        await ctx.send(f"Please verify yourself by clicking the link in your email")

    async def verify_user_loop(self):
        """
        Loop updating roles for those who have clicked the link/verified in some way
        """
        while not self.bot.is_closed():
            newly_verified = self.DBmanager.db_execute_select(
                "SELECT guild_id, user_id, domain FROM verified_users WHERE verified=? AND role_assigned=?",
                (1, 0))
            for guild_id, user_id, domain in newly_verified:
                guild = self.bot.get_guild(guild_id)
                member = guild.get_member(user_id)
                role_id = self.DBmanager.db_execute_select(
                    "SELECT role_id FROM server_info WHERE guild_id=? AND domain=?",
                    (guild_id, domain))
                await member.add_roles(guild.get_role(role_id))
                self.DBmanager.db_execute_commit(
                    "UPDATE verified_users SET role_assigned=? WHERE guild_id=? AND user_id=?",
                    (1, guild_id, user_id))
            await asyncio.sleep(10)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Verification(bot))
