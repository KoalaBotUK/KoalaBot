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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# Libs
import discord
from discord.ext import commands
from sqlalchemy import select, delete, and_, text

# Own modules
import koalabot
from koala.db import session_manager, insert_extension
from koala.errors import InvalidArgumentError
from . import core, errors
from .env import GMAIL_EMAIL, GMAIL_PASSWORD
from .errors import VerifyException
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


class Verification(commands.Cog, name="Verify"):

    def __init__(self, bot):
        self.bot = bot
        insert_extension("Verify", 0, True, True)

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
Please verify one of the following emails to get the appropriate role using \
`{koalabot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers."""
                await member.send(
                    content=message_string + "\n" + "\n".join([f"`{x}` for `@{y}`" for x, y in roles.items()]))

    @commands.check(koalabot.is_admin)
    @commands.command(name="verifyAdd", aliases=["addVerification"])
    @commands.check(verify_is_enabled)
    async def enable_verification(self, ctx: commands.Context, suffix: str, role: discord.Role):
        """
        Set up a role and email pair for KoalaBot to verify users with
        :param ctx: context of the discord message
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role to give users with that email verified (e.g. @students)
        :return:
        """
        await core.add_verify_role(ctx.guild.id, suffix, role.id, self.bot)
        await ctx.send(f"Verification enabled for {role} for emails ending with `{suffix}`")

    @commands.check(koalabot.is_admin)
    @commands.command(name="verifyRemove", aliases=["removeVerification"])
    @commands.check(verify_is_enabled)
    async def disable_verification(self, ctx, suffix: str, role: discord.Role):
        """
        Disable an existing verification listener
        :param ctx: context of the discord message
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role paired with the email (e.g. @students)
        :return:
        """
        core.remove_verify_role(ctx.guild.id, suffix, role.id)

        await ctx.send(f"Emails ending with {suffix} no longer give {role}")

    @commands.check(koalabot.is_admin)
    @commands.command(name="verifyBlacklist")
    @commands.check(verify_is_enabled)
    async def blacklist(self, ctx, user: discord.Member, role: discord.Role, suffix: str):
        await core.blacklist_member(user.id, ctx.guild.id, role.id, suffix, self.bot)
        await ctx.send(f"{user} will no longer receive {role} upon verifying with this email suffix")

    @commands.check(koalabot.is_admin)
    @commands.command(name="verifyBlacklistRemove")
    @commands.check(verify_is_enabled)
    async def blacklist_remove(self, ctx, user: discord.Member, role: discord.Role, suffix: str):
        await core.remove_blacklist_member(user.id, ctx.guild.id, role.id, suffix, self.bot)
        await ctx.send(f"{user} will now be able to receive {role} upon verifying with this email suffix")

    @commands.check(koalabot.is_dm_channel)
    @commands.command(name="verify")
    async def verify(self, ctx, email: str):
        """
        Send to KoalaBot in dms to verify an email with our system
        :param ctx: the context of the discord message
        :param email: the email you want to verify
        :return:
        """
        try:
            await core.email_verify_send(ctx.author.id, email, self.bot)
        except errors.VerifyExistsException as e:
            await ctx.send(e.__str__()+" Would you like to verify anyway? (y/n)")

            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            msg = await self.bot.wait_for('message', check=check)
            if msg.content.lower() == "y" or msg.content.lower() == "yes":
                await core.email_verify_send(ctx.author.id, email, self.bot, force=True)
            else:
                await ctx.send(f"Okay, you will not be verified with {email}")
                return
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
        with session_manager() as session:
            entry = session.execute(select(VerifiedEmails).filter_by(u_id=ctx.author.id, email=email)).all()

            if not entry:
                raise VerifyException("You have not verified that email")

            session.execute(delete(VerifiedEmails).filter_by(u_id=ctx.author.id, email=email))
            session.commit()

            await core.remove_roles_for_user(ctx.author.id, email, self.bot)
            await ctx.send(f"{email} has been un-verified and relevant roles have been removed")

    @commands.check(koalabot.is_dm_channel)
    @commands.command(name="confirm")
    async def confirm(self, ctx, token):
        """
        Send to KoalaBot in dms to confirm the verification of an email
        :param ctx: the context of the discord message
        :param token: the token emailed to you to verify with
        :return:
        """
        with session_manager() as session:
            entry = session.execute(select(NonVerifiedEmails).filter_by(token=token, u_id=ctx.author.id)).scalar()

            if not entry:
                raise InvalidArgumentError("That is not a valid token")

            session.add(VerifiedEmails(u_id=ctx.author.id, email=entry.email))

            session.execute(delete(NonVerifiedEmails).filter_by(token=token, u_id=ctx.author.id))

            potential_roles = session.execute(select(Roles.r_id)
                                              .where(text(":email like ('%' || email_suffix)")),
                                              {"email": entry.email}).all()
            if potential_roles:
                for role_id in potential_roles:
                    session.execute(delete(ToReVerify).filter_by(r_id=role_id[0], u_id=ctx.author.id))

            session.commit()
            await ctx.send("Your email has been verified, thank you")
            await core.assign_roles_for_user(ctx.author.id, entry.email, self.bot)

    @commands.check(koalabot.is_owner)
    @commands.command(name="getEmails")
    async def get_emails(self, ctx, user_id: int):
        """
        See the emails a user is verified with
        :param ctx: the context of the discord message
        :param user_id: the id of the user who's emails you want to find
        :return:
        """
        with session_manager() as session:
            results = session.execute(select(VerifiedEmails.email).filter_by(u_id=user_id)).all()

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
                except AttributeError:
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
                raise VerifyException("Verification is not enabled for that role")
            existing_reverify = session.execute(select(ToReVerify.u_id).filter_by(r_id=role.id)).scalars().all()
            for member in role.members:
                await member.remove_roles(role)
                if member.id not in existing_reverify:
                    session.add(ToReVerify(u_id=member.id, r_id=role.id))

            session.commit()
            await ctx.send("That role has now been removed from all users and they will need to "
                           "re-verify the associated email.")

    async def assign_roles_on_startup(self):
        with session_manager() as session:
            results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)).all()
            for g_id, r_id, suffix in results:
                try:
                    guild = self.bot.get_guild(g_id)
                    role = discord.utils.get(guild.roles, id=r_id)
                    await core.assign_role_to_guild(guild, role, suffix)
                except AttributeError as e:
                    # bot not in guild
                    logger.error("Verify bot not in guild %s", guild.id, exc_info=e)
                except VerifyException as e:
                    logger.error(f"Guild {g_id} has not given Koala sufficient permissions to give roles", exc_info=e)


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the koalabot.
    :param bot: the bot client for KoalaBot
    """
    if GMAIL_EMAIL is None or GMAIL_PASSWORD is None:
        logger.warning("Verification not started. API keys not found in environment.")
        insert_extension("Verify", 0, False, False)
    else:
        await bot.add_cog(Verification(bot))
        logger.info("Verification is ready.")
