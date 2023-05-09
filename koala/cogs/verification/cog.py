#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
from discord.ext import commands

# Own modules
import koalabot
from koala.db import insert_extension
from . import core, errors
from .env import GMAIL_EMAIL, GMAIL_PASSWORD
from .log import logger


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
        await core.assign_roles_on_startup(self.bot)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Assigns necessary roles to users upon joining a server
        :param member: the member object who just joined a server
        :return:
        """
        await core.send_verify_intro_message(member)

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
        await core.email_verify_remove(ctx.author.id, email, self.bot)
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
        await core.email_verify_confirm(ctx.author.id, token, self.bot)
        await ctx.send("Your email has been verified, thank you")

    @commands.check(koalabot.is_owner_ctx)
    @commands.command(name="getEmails")
    async def get_emails(self, ctx, user_id: int):
        """
        See the emails a user is verified with
        :param ctx: the context of the discord message
        :param user_id: the id of the user whose emails you want to find
        :return:
        """
        emails = '\n'.join(core.email_verify_list(user_id))
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
        role_dict = core.grouped_list_verify_role(ctx.guild.id, self.bot)

        for rd_suffix, rd_roles in role_dict.items():
            embed.add_field(name=rd_suffix, value='\n'.join(rd_roles))

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
        await core.re_verify_role(ctx.guild.id, role.id, self.bot)
        await ctx.send("That role has now been removed from all users and they will need to "
                       "re-verify the associated email.")


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    if GMAIL_EMAIL is None or GMAIL_PASSWORD is None:
        logger.warning("Verification not started. API keys not found in environment.")
        insert_extension("Verify", 0, False, False)
    else:
        await bot.add_cog(Verification(bot))
        logger.info("Verification is ready.")
