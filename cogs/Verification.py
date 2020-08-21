#!/usr/bin/env python

"""
TODO
add proper admin checks
add list emails for admins
attempt to add all roles necessary on startup
change that database diagram
add thing to extension table
add new gmail account details to config
add re-verification functionality
"""

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
import string
import smtplib
from email.message import EmailMessage

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager


# Constants

# Variables

def is_dm_channel(ctx):
    return ctx.channel.id == ctx.author.dm_channel.id


def send_email(email, token):
    email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    email_server.ehlo()
    username = "email"
    password = "password"

    msg = EmailMessage()
    msg.set_content(f"Please send the bot the command:\n\n{KoalaBot.COMMAND_PREFIX}confirm {token}")
    msg['Subject'] = "Koalabot Verification"
    msg['From'] = username
    msg['To'] = email

    email_server.login(username, password)
    email_server.send_message(msg)
    email_server.quit()


class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)
        self.DBManager.db_execute_commit("CREATE TABLE IF NOT EXISTS verified_emails (u_id, email)")
        self.DBManager.db_execute_commit("CREATE TABLE IF NOT EXISTS non_verified_emails (u_id, email, token)")
        self.DBManager.db_execute_commit("CREATE TABLE IF NOT EXISTS to_re_verify (u_id, r_id)")
        self.DBManager.db_execute_commit("CREATE TABLE IF NOT EXISTS roles (s_id, r_id, email_suffix)")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        potential_emails = self.DBManager.db_execute_select("SELECT r_id, email_suffix FROM roles WHERE s_id=?",
                                                            (member.guild.id,))
        for role_id, suffix in potential_emails:
            results = self.DBManager.db_execute_select("SELECT * FROM verified_emails WHERE email LIKE ('%' || ?) AND u_id=?",
                                                       (suffix, member.id))
            if results:
                role = discord.utils.get(member.guild.roles, id=role_id)
                await member.add_roles(role)

    @commands.command(name="enable_verification")
    async def enable_verification(self, ctx, suffix=None, role=None):

        if not role or not suffix:
            await ctx.send(
                f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")
            return

        try:
            role_id = int(role[3:-1])
        except ValueError:
            await ctx.send(f"Please give a role by @mentioning it")
            return
        except TypeError:
            await ctx.send("Please give a role by @mentioning it")
            return

        role_valid = discord.utils.get(ctx.guild.roles, id=role_id)
        if not role_valid:
            await ctx.send("Please supply a valid role")
            return

        exists = self.DBManager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=? AND email_suffix=?",
                                                  (ctx.guild.id, role_id, suffix))
        if exists:
            await ctx.send("Verification is already enabled for that role")
            return

        self.DBManager.db_execute_commit("INSERT INTO roles VALUES (?, ?, ?)",
                                         (ctx.guild.id, role_id, suffix))

        await ctx.send(f"Verification enabled for {role} for emails ending with `{suffix}`")
        await self.assign_role_to_guild(ctx.guild, role_valid, suffix)

    @commands.command(name="disable_verification")
    async def disable_verification(self, ctx, suffix=None, role=None):
        if not role or not suffix:
            await ctx.send(
                f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")
            return

        try:
            role_id = int(role[3:-1])
        except ValueError:
            await ctx.send(f"Please give a role by @mentioning it")
            return
        except TypeError:
            await ctx.send("Please give a role by @mentioning it")
            return

        self.DBManager.db_execute_commit("DELETE FROM roles WHERE s_id=? AND r_id=? AND email_suffix=?",
                                         (ctx.guild.id, role_id, suffix))
        await ctx.send(f"Emails ending with {suffix} no longer give {role}")

    @commands.check(is_dm_channel)
    @commands.command(name="verify")
    async def verify(self, ctx, email):
        already_verified = self.DBManager.db_execute_select("SELECT * FROM verified_emails WHERE u_id=? AND email=?",
                                                  (ctx.author.id, email))
        if already_verified:
            await ctx.send("That email is already verified")
            return

        verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        self.DBManager.db_execute_commit("INSERT INTO non_verified_emails VALUES (?, ?, ?)",
                                         (ctx.author.id, email, verification_code))
        send_email(email, verification_code)
        await ctx.send("Please verify yourself using the command you have been emailed")

    @commands.check(is_dm_channel)
    @commands.command(name="confirm")
    async def confirm(self, ctx, token):
        entry = self.DBManager.db_execute_select("SELECT * FROM non_verified_emails WHERE token=?",
                                                 (token,))
        if not entry:
            await ctx.send("That is not a valid token")
            return

        self.DBManager.db_execute_commit("INSERT INTO verified_emails VALUES (?, ?)",
                                         (entry[0][0], entry[0][1]))
        self.DBManager.db_execute_commit("DELETE FROM non_verified_emails WHERE token=?",
                                         (token,))
        await ctx.send("Your email has been verified, thank you")
        await self.assign_roles_for_user(ctx.author.id, entry[0][1])

    async def assign_roles_for_user(self, user_id, email):
        results = self.DBManager.db_execute_select("SELECT * FROM roles WHERE ? like ('%' || email_suffix)",
                                                   (email,))
        for g_id, r_id, suffix in results:
            guild = self.bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            await member.add_roles(role)

    async def assign_role_to_guild(self, guild, role, suffix):
        results = self.DBManager.db_execute_select("SELECT u_id FROM verified_emails WHERE email LIKE ('%' || ?)",
                                                   (suffix,))
        for user_id in results:
            try:
                member = guild.get_member(user_id[0])
                await member.add_roles(role)
            except AttributeError:
                pass

def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Verification(bot))
