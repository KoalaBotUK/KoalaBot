#!/usr/bin/env python

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
GMAIL_EMAIL = os.environ.get('GMAIL_EMAIL')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
# Variables




def verify_is_enabled(ctx):
    """
    A command used to check if the guild has enabled verify
    e.g. @commands.check(verify_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Verify")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)

class Verification(commands.Cog, name="Verify"):

    def __init__(self, bot, db_manager=None):
        self.bot = bot
        if not db_manager:
            self.DBManager = KoalaBot.database_manager
            self.set_up_tables()
            self.DBManager.insert_extension("Verify", 0, True, True)
        else:
            self.DBManager = db_manager

    def set_up_tables(self):
        """
        Creates tables necessary for verification cog to function
        :return:
        """
        verified_table = """
        CREATE TABLE IF NOT EXISTS verified_emails (
        u_id integer NOT NULL,
        email text NOT NULL,
        PRIMARY KEY (u_id, email)
        );
        """

        non_verified_table = """
        CREATE TABLE IF NOT EXISTS non_verified_emails (
        u_id integer NOT NULL,
        email text NOT NULL,
        token text NOT NULL,
        PRIMARY KEY (token)
        );
        """

        role_table = """
        CREATE TABLE IF NOT EXISTS roles (
        s_id integer NOT NULL,
        r_id integer NOT NULL,
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
        """
        Sends an email through gmails smtp server from the email stored in the environment variables
        :param email: target to send an email to
        :param token: the token the recipient will need to verify with
        :return:
        """
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
        """
        Assigns necessary roles to users upon joining a server
        :param member: the member object who just joined a server
        :return:
        """
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
Please verify one of the following emails to get the appropriate role using `{KoalaBot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers."""
            await member.send(
                content=message_string + "\n" + "\n".join([f"`{x}` for `@{y}`" for x, y in roles.items()]))

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="verifyAdd", aliases=["addVerification"])
    @commands.check(verify_is_enabled)
    async def enable_verification(self, ctx, suffix=None, role=None):
        """
        Set up a role and email pair for KoalaBot to verify users with
        :param ctx: context of the discord message
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role to give users with that email verified (e.g. @students)
        :return:
        """
        if not role or not suffix:
            raise self.InvalidArgumentError(f"Please provide the correct arguments\n(`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")

        try:
            role_id = int(role[3:-1])
        except ValueError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")
        except TypeError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")

        role_valid = discord.utils.get(ctx.guild.roles, id=role_id)
        if not role_valid:
            raise self.InvalidArgumentError("Please mention a role in this guild")

        exists = self.DBManager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=? AND email_suffix=?",
                                                  (ctx.guild.id, role_id, suffix))
        if exists:
            raise self.VerifyError("Verification is already enabled for that role")

        self.DBManager.db_execute_commit("INSERT INTO roles VALUES (?, ?, ?)",
                                         (ctx.guild.id, role_id, suffix))

        await ctx.send(f"Verification enabled for {role} for emails ending with `{suffix}`")
        await self.assign_role_to_guild(ctx.guild, role_valid, suffix)

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="verifyRemove", aliases=["removeVerification"])
    @commands.check(verify_is_enabled)
    async def disable_verification(self, ctx, suffix=None, role=None):
        """
        Disable an existing verification listener
        :param ctx: context of the discord message
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role paired with the email (e.g. @students)
        :return:
        """
        if not role or not suffix:
            raise self.InvalidArgumentError(
                f"Please provide the correct arguments\n(`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")

        try:
            role_id = int(role[3:-1])
        except ValueError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")
        except TypeError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")

        self.DBManager.db_execute_commit("DELETE FROM roles WHERE s_id=? AND r_id=? AND email_suffix=?",
                                         (ctx.guild.id, role_id, suffix))
        await ctx.send(f"Emails ending with {suffix} no longer give {role}")


    @commands.check(KoalaBot.is_dm_channel)
    @commands.command(name="verify")
    async def verify(self, ctx, email):
        """
        Send to KoalaBot in dms to verify an email with our system
        :param ctx: the context of the discord message
        :param email: the email you want to verify
        :return:
        """
        already_verified = self.DBManager.db_execute_select("SELECT * FROM verified_emails WHERE email=?",
                                                            (email,))
        in_blacklist = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE u_id=?",
                                                        (ctx.author.id,))
        if already_verified and not in_blacklist:
            raise self.VerifyError("That email is already verified")

        verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        self.DBManager.db_execute_commit("INSERT INTO non_verified_emails VALUES (?, ?, ?)",
                                         (ctx.author.id, email, verification_code))
        self.send_email(email, verification_code)
        await ctx.send("Please verify yourself using the command you have been emailed")

    @commands.check(KoalaBot.is_dm_channel)
    @commands.command(name="unVerify")
    async def un_verify(self, ctx, email):
        """
        Send to KoalaBot in dms to un-verify an email with our system
        :param ctx: the context of the discord message
        :param email: the email you want to un-verify
        :return:
        """
        entry = self.DBManager.db_execute_select("SELECT * FROM verified_emails WHERE u_id=? AND email=?",
                                                 (ctx.author.id, email))
        if not entry:
            raise self.VerifyError("You have not verified that email")

        self.DBManager.db_execute_commit("DELETE FROM verified_emails WHERE u_id=? AND email=?",
                                         (ctx.author.id, email))
        await self.remove_roles_for_user(ctx.author.id, email)
        await ctx.send(f"{email} has been un-verified and relevant roles have been removed")

    @commands.check(KoalaBot.is_dm_channel)
    @commands.command(name="confirm")
    async def confirm(self, ctx, token):
        """
        Send to KoalaBot in dms to confirm the verification of an email
        :param ctx: the context of the discord message
        :param token: the token emailed to you to verify with
        :return:
        """
        entry = self.DBManager.db_execute_select("SELECT * FROM non_verified_emails WHERE token=?",
                                                 (token,))
        if not entry:
            raise self.InvalidArgumentError("That is not a valid token")

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
        See the emails a user is verified with
        :param ctx: the context of the discord message
        :param user_id: the id of the user who's emails you want to find
        :return:
        """
        results = self.DBManager.db_execute_select("SELECT email FROM verified_emails WHERE u_id=?", (user_id,))
        emails = '\n'.join([x[0] for x in results])
        await ctx.send(f"This user has registered with:\n{emails}")

    @commands.command(name="verifyList", aliases=["checkVerifications"])
    @commands.check(verify_is_enabled)
    async def check_verifications(self, ctx):
        """
        List the current verification setup for the server
        :param ctx: the context of the discord message
        :return:
        """
        embed = discord.Embed(title=f"Current verification setup for {ctx.guild.name}")
        roles = self.DBManager.db_execute_select("SELECT r_id, email_suffix FROM roles WHERE s_id=?",
                                                 (ctx.guild.id,))
        role_dict = {}
        for role_id, suffix in roles:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            try:
                if suffix in role_dict:
                    role_dict[suffix].append("@" + role.name)
                else:
                    role_dict[suffix] = ["@" + role.name]
            except AttributeError as e:
                self.DBManager.db_execute_commit("DELETE FROM roles WHERE r_id=?", (role_id,))

        for suffix, roles in role_dict.items():
            embed.add_field(name=suffix, value='\n'.join(roles))

        await ctx.send(embed=embed)

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="reVerify")
    @commands.check(verify_is_enabled)
    async def re_verify(self, ctx, role):
        """
        Removes a role from all users who have it and marks them as needing to re-verify before giving it back
        :param ctx: the context of the discord message
        :param role: the role to be removed and re-verified (e.g. @students)
        :return:
        """
        try:
            role_id = int(role[3:-1])
        except ValueError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")
        except TypeError:
            raise self.InvalidArgumentError("Please give a role by @mentioning it")

        exists = self.DBManager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=?",
                                                  (ctx.guild.id, role_id))
        if not exists:
            raise self.VerifyError("Verification is not enabled for that role")
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_roles(role)
                self.DBManager.db_execute_commit("INSERT INTO to_re_verify VALUES (?, ?)",
                                                 (member.id, role.id))
        await ctx.send("That role has now been removed from all users and they will need to re-verify the associated email.")

    class InvalidArgumentError(Exception):
        pass

    class VerifyError(Exception):
        pass

    async def assign_roles_on_startup(self):
        results = self.DBManager.db_execute_select("SELECT * FROM roles")
        for g_id, r_id, suffix in results:
            try:
                guild = self.bot.get_guild(g_id)
                role = discord.utils.get(guild.roles, id=r_id)
                await self.assign_role_to_guild(guild, role, suffix)
            except AttributeError as e:
                # bot not in guild
                print(e)

    async def assign_roles_for_user(self, user_id, email):
        results = self.DBManager.db_execute_select("SELECT * FROM roles WHERE ? like ('%' || email_suffix)",
                                                   (email,))
        for g_id, r_id, suffix in results:
            blacklisted = self.DBManager.db_execute_select("SELECT * FROM to_re_verify WHERE r_id=? AND u_id=?",
                                                           (r_id, user_id))
            if blacklisted:
                continue
            try:
                guild = self.bot.get_guild(g_id)
                role = discord.utils.get(guild.roles, id=r_id)
                member = guild.get_member(user_id)
                if not member:
                    member = await guild.fetch_member(user_id)
                await member.add_roles(role)
            except AttributeError as e:
                # bot not in guild
                print(e)
            except discord.errors.NotFound:
                print(f"user with id {user_id} not found")

    async def remove_roles_for_user(self, user_id, email):
        results = self.DBManager.db_execute_select("SELECT * FROM roles WHERE ? like ('%' || email_suffix)",
                                                   (email,))
        for g_id, r_id, suffix in results:
            try:
                guild = self.bot.get_guild(g_id)
                role = discord.utils.get(guild.roles, id=r_id)
                member = guild.get_member(user_id)
                if not member:
                    member = await guild.fetch_member(user_id)
                await member.remove_roles(role)
            except AttributeError as e:
                # bot not in guild
                print(e)
            except discord.errors.NotFound:
                print(f"user with id {user_id} not found in {guild}")

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
                if not member:
                    member = await guild.fetch_member(user_id[0])
                await member.add_roles(role)
            except AttributeError as e:
                # bot not in guild
                print(e)
            except discord.errors.NotFound:
                print(f"user with id {user_id} not found in {guild}")


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    if GMAIL_EMAIL is None or GMAIL_PASSWORD is None:
        print("Verification not started. API keys not found in environment.")
        KoalaBot.database_manager.insert_extension("Verify", 0, False, False)
    else:
        bot.add_cog(Verification(bot))
        print("Verification is ready.")

