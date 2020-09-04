#!/usr/bin/env python

"""
TODO
change that database diagram
add re-verification functionality - probably done
do tests oh no
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
from dotenv import load_dotenv
import os

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager


# Constants
load_dotenv()
GMAIL_EMAIL = os.environ['GMAIL_EMAIL']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']

# Variables

def is_dm_channel(ctx):
    return ctx.channel.id == ctx.author.dm_channel.id


class Verification(commands.Cog):

    def __init__(self, bot, db_manager=None):
        self.bot = bot
        if not db_manager:
            self.DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)
            self.set_up_tables()
            self.DBManager.insert_extension("Verification", 0, True, True)
        else:
            self.DBManager = db_manager

    def set_up_tables(self):
        verified_table = """
        CREATE TABLE IF NOT EXISTS verified_emails (
        u_id integer NOT NULL,
        email text NOT NULL,
        PRIMARY KEY (u_id, email)
        );
        """

        non_verified_table = """
        CREATE TABLE IF NOT EXISTS verified_emails (
        u_id integer NOT NULL,
        email text NOT NULL,
        token text NOT NULL,
        PRIMARY KEY (token)
        );
        """

        role_table = """
        CREATE TABLE IF NOT EXISTS roles (
        s_id integer NOT NULL,
        r_id text NOT NULL,
        email_suffix text NOT NULL,
        PRIMARY KEY (s_id, r_id, email_suffix),
        FOREIGN KEY (s_id) REFERENCES GuildExtensions (guild_id)
        );
        """

        re_verify_table = """
        CREATE TABLE IF NOT EXISTS to_re_verify (
        u_id integer NOT NULL,
        r_id text NOT NULL,
        PRIMARY KEY (u_id, r_id)
        );
        """

        self.DBManager.db_execute_commit(verified_table)
        self.DBManager.db_execute_commit(non_verified_table)
        self.DBManager.db_execute_commit(role_table)
        self.DBManager.db_execute_commit(re_verify_table)

    @staticmethod
    def send_email(email, token):
        email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        email_server.ehlo()
        username = GMAIL_EMAIL
        password = GMAIL_PASSWORD

        msg = EmailMessage()
        msg.set_content(f"Please send the bot the command:\n\n{KoalaBot.COMMAND_PREFIX}confirm {token}")
        msg['Subject'] = "Koalabot Verification"
        msg['From'] = username
        msg['To'] = email

        email_server.login(username, password)
        email_server.send_message(msg)
        email_server.quit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.assign_roles_on_startup()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        potential_emails = self.DBManager.db_execute_select("SELECT r_id, email_suffix FROM roles WHERE s_id=?",
                                                            (member.guild.id,))
        if potential_emails:
            roles = {}
            for role_id, suffix in potential_emails:
                role = discord.utils.get(member.guild.roles, id=role_id)
                roles[suffix] = role
                results = self.DBManager.db_execute_select(
                    "SELECT * FROM verified_emails WHERE email LIKE ('%' || ?) AND u_id=?",
                    (suffix, member.id))

                blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                               (role_id, member.id))
                if results and not blacklisted:
                    await member.add_roles(role)
            message_string = f"""Welcome to {member.guild.name}. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role.
This email is stored so you don't need to verify it multiple times."""
            await member.send(content=message_string + "\n" + "\n".join([f"{x} for @{y}" for x, y in roles.items()]))

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="enableVerification")
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

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="disableVerification")
    async def disable_verification(self, ctx, suffix=None, role=None):
        if not role or not suffix:
            await ctx.send(
                f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}disable_verification <domain> <@role>`")
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
        in_blacklist = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE u_id=?",
                                                        (ctx.author.id,))
        if already_verified and not in_blacklist:
            await ctx.send("That email is already verified")
            return

        verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        self.DBManager.db_execute_commit("INSERT INTO non_verified_emails VALUES (?, ?, ?)",
                                         (ctx.author.id, email, verification_code))
        self.send_email(email, verification_code)
        await ctx.send("Please verify yourself using the command you have been emailed")

    @commands.check(is_dm_channel)
    @commands.command(name="confirm")
    async def confirm(self, ctx, token):

        entry = self.DBManager.db_execute_select("SELECT * FROM non_verified_emails WHERE token=?",
                                                 (token,))
        if not entry:
            await ctx.send("That is not a valid token")
            return

        already_verified = self.DBManager.db_execute_select("SELECT * FROM verified_emails WHERE u_id=? AND email=?",
                                                            (ctx.author.id, entry[0][1]))
        if not already_verified:
            self.DBManager.db_execute_commit("INSERT INTO verified_emails VALUES (?, ?)",
                                             (entry[0][0], entry[0][1]))
        self.DBManager.db_execute_commit("DELETE FROM non_verified_emails WHERE token=?",
                                         (token,))
        potential_roles = self.DBManager.db_execute_select("SELECT r_id FROM roles WHERE ? LIKE ('%' || email_suffix)",
                                                           (entry[0][1],))
        if potential_roles:
            for role_id in potential_roles:
                self.DBManager.db_execute_commit("DELETE FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                 (role_id[0], ctx.author.id))
        await ctx.send("Your email has been verified, thank you")
        await self.assign_roles_for_user(ctx.author.id, entry[0][1])

    @commands.check(KoalaBot.is_owner)
    @commands.command(name="getEmails")
    async def get_emails(self, ctx, user_id: int):
        """
        Unused until theres an unabusable way to do it
        # roles = self.DBManager.db_execute_select("SELECT r_id, email_suffix FROM roles WHERE s_id=?",
        #                                          (ctx.guild.id,))
        # emails = []
        # member = ctx.guild.get_member(user_id)
        # for r_id, suffix in roles:
        #     role = discord.utils.get(ctx.guild.roles, id=r_id)
        #     if role not in member.roles:
        #         continue
        #     results = self.DBManager.db_execute_select("SELECT email FROM verified_emails WHERE u_id=? AND email LIKE ('%' || ?)",
        #                                                 (user_id, suffix))
        #     for result in results:
        #         emails.append(result[0])
        #
        """
        results = self.DBManager.db_execute_select("SELECT email FROM verified_emails WHERE u_id=?", (user_id,))
        emails = '\n'.join([x[0] for x in results])
        await ctx.send(f"This user has registered with:\n{emails}")

    @commands.command(name="checkVerifications")
    async def check_verifications(self, ctx):
        embed = discord.Embed(title=f"Current verification setup for {ctx.guild.name}")
        roles = self.DBManager.db_execute_select("SELECT r_id, email_suffix FROM roles WHERE s_id=?",
                                                 (ctx.guild.id,))
        role_dict = {}
        for role_id, suffix in roles:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            if suffix in role_dict:
                role_dict[suffix].append("@" + role.name)
            else:
                role_dict[suffix] = ["@" + role.name]

        for suffix, roles in role_dict.items():
            embed.add_field(name=suffix, value='\n'.join(roles))

        await ctx.send(embed=embed)

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="reVerify")
    async def re_verify(self, ctx, role):
        """Removes all instances of a role"""
        try:
            role_id = int(role[3:-1])
        except ValueError:
            await ctx.send(f"Please give a role by @mentioning it")
            return
        except TypeError:
            await ctx.send("Please give a role by @mentioning it")
            return

        exists = self.DBManager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=?",
                                                  (ctx.guild.id, role_id))
        if not exists:
            await ctx.send("Verification is not enabled for that role")
            return

        role = discord.utils.get(ctx.guild.roles, id=role_id)
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_roles(role)
                self.DBManager.db_execute_commit("INSERT INTO to_re_verify VALUES (?, ?)",
                                                 (member.id, role.id))

    async def assign_roles_on_startup(self):
        results = self.DBManager.db_execute_select("SELECT * FROM roles")
        for g_id, r_id, suffix in results:
            guild = self.bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            await self.assign_role_to_guild(guild, role, suffix)

    async def assign_roles_for_user(self, user_id, email):
        results = self.DBManager.db_execute_select("SELECT * FROM roles WHERE ? like ('%' || email_suffix)",
                                                   (email,))
        for g_id, r_id, suffix in results:
            blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                           (r_id, user_id))
            if blacklisted:
                continue

            guild = self.bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            await member.add_roles(role)

    async def assign_role_to_guild(self, guild, role, suffix):
        results = self.DBManager.db_execute_select("SELECT u_id FROM verified_emails WHERE email LIKE ('%' || ?)",
                                                   (suffix,))
        for user_id in results:
            try:
                blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                               (role.id, user_id[0]))
                if blacklisted:
                    continue

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
