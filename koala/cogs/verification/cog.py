#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
from discord import Button, ButtonStyle, app_commands
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
    verify_group = app_commands.Group(name="verify", description="lmao get verified")

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
    @verify_group.command(name="add", description="Set up a role and email pair to verify users with")
    @commands.check(verify_is_enabled)
    async def enable_verification(self, interaction: discord.Interaction, suffix: str, role: discord.Role):
        """
        Set up a role and email pair for KoalaBot to verify users with
        :param interaction:
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role to give users with that email verified (e.g. @students)
        :return:
        """
        await core.add_verify_role(interaction.guild_id, suffix, role.id, self.bot)
        await interaction.response.send_message(f"Verification enabled for {role} for emails ending with `{suffix}`")

    @commands.check(koalabot.is_admin)
    @verify_group.command(name="remove", description="Disable an existing verification pair")
    @commands.check(verify_is_enabled)
    async def disable_verification(self, interaction: discord.Interaction, suffix: str, role: discord.Role):
        """
        Disable an existing verification listener
        :param interaction:
        :param suffix: end of the email (e.g. "example.com")
        :param role: the role paired with the email (e.g. @students)
        :return:
        """
        core.remove_verify_role(interaction.guild_id, suffix, role.id)

        await interaction.response.send_message(f"Emails ending with {suffix} no longer give {role}")

    @commands.check(koalabot.is_admin)
    @verify_group.command(name="blacklist", description="Prevent a user from receiving a specific role")
    @commands.check(verify_is_enabled)
    async def blacklist(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role, suffix: str):
        await core.blacklist_member(user.id, interaction.guild_id, role.id, suffix, self.bot)
        await interaction.response.send_message(f"{user} will no longer receive {role} upon verifying with this email suffix")

    @commands.check(koalabot.is_admin)
    @verify_group.command(name="blacklistremove", description="Lift a blacklist restriction on a user")
    @commands.check(verify_is_enabled)
    async def blacklist_remove(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role, suffix: str):
        await core.remove_blacklist_member(user.id, interaction.guild_id, role.id, suffix, self.bot)
        await interaction.response.send_message(f"{user} will now be able to receive {role} upon verifying with this email suffix")

    @commands.check(koalabot.is_dm_channel)
    @verify_group.command(name="me", description="Verify an email")
    async def verify(self, interaction: discord.Interaction, email: str):
        """
        Send to KoalaBot in dms to verify an email with our system
        :param interaction:
        :param email: the email you want to verify
        :return:
        """
        try:
            await interaction.response.defer()
            await core.email_verify_send(interaction.user.id, email, self.bot)

        except errors.VerifyExistsException as e:
            # embed: discord.Embed = discord.Embed(title="Verify Exists", description=e.__str__()+" Would you like to verify anyway?")

            # await interaction.response.send_message(embed=embed, components=[Button(ButtonStyle.green, custom_id="yesButton", label="Yes"), Button(ButtonStyle.red, custom_id="noButton", label="No")])

            await interaction.followup.send_message(e.__str__()+" Would you like to verify anyway? (y/n)")

            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            msg = await self.bot.wait_for('message', check=check)
            if msg.content.lower() == "y" or msg.content.lower() == "yes":
                await core.email_verify_send(interaction.user.id, email, self.bot, force=True)
            else:
                await interaction.followup.send_message(f"Okay, you will not be verified with {email}")
                return
        await interaction.followup.send_message("Please verify yourself using the command you have been emailed", ephemeral=True)


    @commands.check(koalabot.is_dm_channel)
    @verify_group.command(name="unverify", description="Unverify an email")
    async def un_verify(self, interaction: discord.Interaction, email: str):
        """
        Send to KoalaBot in dms to un-verify an email with our system
        :param interaction:
        :param email: the email you want to un-verify
        :return:
        """
        await core.email_verify_remove(interaction.user.id, email, self.bot)
        await interaction.response.send_message(f"{email} has been un-verified and relevant roles have been removed", ephemeral=True)


    @commands.check(koalabot.is_dm_channel)
    @verify_group.command(name="confirm", description="Confirm verification of an email")
    async def confirm(self, interaction: discord.Interaction, token: str):
        """
        Confirm the verification of an email
        :param interaction:
        :param token: the token emailed to you to verify with
        :return:
        """
        await core.email_verify_confirm(interaction.user.id, token, self.bot)
        await interaction.response.send_message("Your email has been verified, thank you", ephemeral=True)


    @commands.check(koalabot.is_owner_ctx)
    @verify_group.command(name="getemails", description="See the emails a user is verified with")
    async def get_emails(self, interaction: discord.Interaction, user_id: str):
        """
        See the emails a user is verified with
        :param interaction:
        :param user_id: the id of the user whose emails you want to find
        :return:
        """
        emails = '\n'.join(core.email_verify_list(int(user_id)))
        await interaction.response.send_message(f"This user has registered with:\n{emails}", ephemeral=True)


    @verify_group.command(name="list", description="List the current verification setup for the server")
    @commands.check(verify_is_enabled)
    async def check_verifications(self, interaction: discord.Interaction):
        """
        List the current verification setup for the server
        :param interaction:
        :return:
        """
        embed = discord.Embed(title=f"Current verification setup for {interaction.guild.name}")
        role_dict = core.grouped_list_verify_role(interaction.guild_id, self.bot)

        for rd_suffix, rd_roles in role_dict.items():
            embed.add_field(name=rd_suffix, value='\n'.join(rd_roles))

        await interaction.response.send_message(embed=embed)


    @commands.check(koalabot.is_admin)
    @verify_group.command(name="reverify", description="Remove a role from all users and marks them as needing to reverify before giving it back")
    @commands.check(verify_is_enabled)
    async def re_verify(self, interaction: discord.Interaction, role: discord.Role):
        """
        Removes a role from all users who have it and marks them as needing to re-verify before giving it back
        :param interaction:
        :param role: the role to be removed and re-verified (e.g. @students)
        :return:
        """
        await core.re_verify_role(interaction.guild_id, role.id, self.bot)
        await interaction.response.send_message("That role has now been removed from all users and they will need to "
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
