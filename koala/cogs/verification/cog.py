#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
import smtplib
import string
from email.message import EmailMessage

# Libs
import discord
from discord.ext import commands
from sqlalchemy import select, delete, and_, text

# Own modules
import koalabot
from koala.db import session_manager, insert_extension
from . import core
from .env import GMAIL_EMAIL, GMAIL_PASSWORD
from .log import logger
from .models import VerifiedEmails, NonVerifiedEmails, Roles, ToReVerify


# Constants

# Variables




def verify_is_enabled(ctx):
    """
    A command used to check if the guild has enabled verify
    e.g. @commands.check(verify_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(ctx, "Verify")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == koalabot.TEST_USER and koalabot.is_dpytest)


# FIXME: Move database commands to db.py
class Verification(commands.Cog, name="Verify"):

    def __init__(self, bot):
        self.bot = bot
        insert_extension("Verify", 0, True, True)

    @staticmethod
    def send_email(email, token):
        """
        Sends an email through gmails smtp server from the email stored in the environment variables
        :param email: target to send an email to
        :param token: the token the recipient will need to verify with
        :return:
        """
        core.send_email(email=email, token=token)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.assign_roles_on_startup()

    @commands.Cog.listener()
    async def on_member_join(self, member): # not sure if this should be in core...
        """
        Assigns necessary roles to users upon joining a server
        :param member: the member object who just joined a server
        :return:
        """
        with session_manager() as session:
            potential_emails = session.execute(select(Roles.r_id, Roles.email_suffix)
                                               .filter_by(s_id=member.guild.id)).all()

            if potential_emails:
                roles = {}
                for role_id, suffix in potential_emails:
                    role = discord.utils.get(member.guild.roles, id=role_id)
                    roles[suffix] = role
                    results = session.execute(select(VerifiedEmails).where(
                        and_(
                            VerifiedEmails.email.endswith(suffix),
                            VerifiedEmails.u_id == member.id
                        ))).all()

                    blacklisted = session.execute(select(ToReVerify)
                                                  .filter_by(r_id=role_id, u_id=member.id)).all()

                    if results and not blacklisted:
                        await member.add_roles(role)
                message_string = f"""Welcome to {member.guild.name}. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using `{koalabot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers."""
                await member.send(
                    content=message_string + "\n" + "\n".join([f"`{x}` for `@{y}`" for x, y in roles.items()]))

    @commands.check(koalabot.is_admin)
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
        role_valid = core.enable_verification(ctx.guild.id, ctx.guild.roles, suffix, role)

        await ctx.send(f"Verification enabled for {role} for emails ending with `{suffix}`")
        await self.assign_role_to_guild(ctx.guild, role_valid, suffix) # switch this to use core func

    @commands.check(koalabot.is_admin)
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
        core.disable_verification(ctx.guild.id, suffix, role)

        await ctx.send(f"Emails ending with {suffix} no longer give {role}")


    @commands.check(koalabot.is_dm_channel)
    @commands.command(name="verify")
    async def verify(self, ctx, email):
        """
        Send to KoalaBot in dms to verify an email with our system
        :param ctx: the context of the discord message
        :param email: the email you want to verify
        :return:
        """
        core.verify(ctx.author.id, email)

        await ctx.send("Please verify yourself using the command you have been emailed")

    @commands.check(koalabot.is_dm_channel)
    @commands.command(name="unVerify")
    async def un_verify(self, ctx, email):
        """
        Send to KoalaBot in dms to un-verify an email with our system
        :param ctx: the context of the discord message
        :param email: the email you want to un-verify
        :return:
        """
        core.un_verify(ctx.author.id, email)

        await self.remove_roles_for_user(ctx.author.id, email)
        await ctx.send(f"{email} has been un-verified and relevant roles have been removed")

    @commands.check(koalabot.is_dm_channel)
    @commands.command(name="confirm")
    async def confirm(self, ctx, token): # not in core?
        """
        Send to KoalaBot in dms to confirm the verification of an email
        :param ctx: the context of the discord message
        :param token: the token emailed to you to verify with
        :return:
        """
        with session_manager() as session:
            entry = session.execute(select(NonVerifiedEmails).filter_by(token=token)).scalar()

            if not entry:
                raise self.InvalidArgumentError("That is not a valid token")

            already_verified = session.execute(select(VerifiedEmails)
                                               .filter_by(u_id=ctx.author.id, email=entry.email)).all()

            if not already_verified:
                session.add(VerifiedEmails(u_id=ctx.author.id, email=entry.email))

            session.execute(delete(NonVerifiedEmails).filter_by(token=token))

            potential_roles = session.execute(select(Roles.r_id)
                                              .where(text(":email like ('%' || email_suffix)")),
                                              {"email": entry.email}).all()
            if potential_roles:
                for role_id in potential_roles:
                    session.execute(delete(ToReVerify).filter_by(r_id=role_id[0], u_id=ctx.author.id))

            session.commit()
            await ctx.send("Your email has been verified, thank you")
            await self.assign_roles_for_user(ctx.author.id, entry.email)

    @commands.check(koalabot.is_owner)
    @commands.command(name="getEmails")
    async def get_emails(self, ctx, user_id: int):
        """
        See the emails a user is verified with
        :param ctx: the context of the discord message
        :param user_id: the id of the user who's emails you want to find
        :return:
        """
        emails = core.get_emails(user_id)
        await ctx.send(f"This user has registered with:\n{emails}")

    @commands.command(name="verifyList", aliases=["checkVerifications"])
    @commands.check(verify_is_enabled)
    async def check_verifications(self, ctx):
        """
        List the current verification setup for the server
        :param ctx: the context of the discord message
        :return:
        """
        with session_manager() as session:
            embed = discord.Embed(title=f"Current verification setup for {ctx.guild.name}")
            roles = session.execute(select(Roles.r_id, Roles.email_suffix).filter_by(s_id=ctx.guild.id)).all()

            role_dict = {}
            for role_id, suffix in roles:
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                try:
                    if suffix in role_dict:
                        role_dict[suffix].append("@" + role.name)
                    else:
                        role_dict[suffix] = ["@" + role.name]
                except AttributeError as e:
                    session.execute(delete(Roles).filter_by(r_id=role_id))

            session.commit()
            for suffix, roles in role_dict.items():
                embed.add_field(name=suffix, value='\n'.join(roles))

            await ctx.send(embed=embed)

    @commands.check(koalabot.is_admin)
    @commands.command(name="reVerify")
    @commands.check(verify_is_enabled)
    async def re_verify(self, ctx, role: discord.Role):
        """
        Removes a role from all users who have it and marks them as needing to re-verify before giving it back
        :param ctx: the context of the discord message
        :param role: the role to be removed and re-verified (e.g. @students)
        :return:
        """
        with session_manager() as session:
            exists = session.execute(select(Roles).filter_by(s_id=ctx.guild.id, r_id=role.id)).all()

            if not exists:
                raise self.VerifyError("Verification is not enabled for that role")
            existing_reverify = session.execute(select(ToReVerify.u_id).filter_by(r_id=role.id)).scalars().all()
            for member in role.members:
                await member.remove_roles(role)
                if member.id not in existing_reverify:
                    session.add(ToReVerify(u_id=member.id, r_id=role.id))

            session.commit()
            await ctx.send("That role has now been removed from all users and they will need to re-verify the associated email.")

    class InvalidArgumentError(Exception):
        pass

    class VerifyError(Exception):
        pass

    async def assign_roles_on_startup(self):
        with session_manager() as session:
            results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)).all()
            for g_id, r_id, suffix in results:
                try:
                    guild = self.bot.get_guild(g_id)
                    role = discord.utils.get(guild.roles, id=r_id)
                    await self.assign_role_to_guild(guild, role, suffix)
                except AttributeError as e:
                    # bot not in guild
                    logger.error(e)

    async def assign_roles_for_user(self, user_id, email):
        with session_manager() as session:
            results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                                      .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

            for g_id, r_id, suffix in results:
                blacklisted = session.execute(select(ToReVerify).filter_by(r_id=r_id, u_id=user_id)).all()

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
                    logger.error(e)
                except discord.errors.NotFound:
                    logger.warn(f"user with id {user_id} not found")

    async def remove_roles_for_user(self, user_id, email):
        with session_manager() as session:
            results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                                      .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

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
                    logger.error(e)
                except discord.errors.NotFound:
                    logger.error(f"user with id {user_id} not found in {guild}")

    async def assign_role_to_guild(self, guild, role, suffix):
        with session_manager() as session:
            results = session.execute(select(VerifiedEmails.u_id).where(VerifiedEmails.email.endswith(suffix))).all()

            for user_id in results:
                try:
                    blacklisted = session.execute(select(ToReVerify).filter_by(r_id=role.id, u_id=user_id[0])).all()

                    if blacklisted:
                        continue
                    member = guild.get_member(user_id[0])
                    if not member:
                        member = await guild.fetch_member(user_id[0])
                    await member.add_roles(role)
                except AttributeError as e:
                    # bot not in guild
                    logger.error(e)
                except discord.errors.NotFound:
                    logger.error(f"user with id {user_id} not found in {guild}")


def setup(bot: koalabot) -> None:
    """
    Load this cog to the koalabot.
    :param bot: the bot client for KoalaBot
    """
    if GMAIL_EMAIL is None or GMAIL_PASSWORD is None:
        logger.warning("Verification not started. API keys not found in environment.")
        insert_extension("Verify", 0, False, False)
    else:
        bot.add_cog(Verification(bot))
        logger.info("Verification is ready.")

