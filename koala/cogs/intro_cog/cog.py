#!/usr/bin/env python

"""
Koala Bot Intro Message Cog Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import asyncio
import discord
from discord.ext import commands

# Own modules
import koalabot

from .log import logger
from .db import get_guild_welcome_message, update_guild_welcome_message, new_guild_welcome_message, \
    remove_guild_welcome_message
from .utils import get_non_bot_members, ask_for_confirmation, wait_for_message, \
    BASE_LEGAL_MESSAGE

# Constants

# Variables


class IntroCog(commands.Cog, name="Intro"):
    """
    A discord.py cog with commands pertaining to the welcome messages that a member will receive
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """
        On bot joining guild, add this guild to the database of guild welcome messages.
        :param guild: Guild KoalaBot just joined
        """
        new_guild_welcome_message(guild.id)
        logger.info(f"KoalaBot joined new guild, id = {guild.id}, name = {guild.name}.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        On member joining guild, send DM to member with welcome message.
        :param member: Member which just joined guild
        """
        await koalabot.dm_group_message([member], get_guild_welcome_message(member.guild.id))
        logger.info(f"New member {member.name} joined guild id {member.guild.id}. Sent them welcome message.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        On bot leaving guild, remove the guild from the database of guild welcome messages
        :param guild: Guild KoalaBot just left
        """
        count = remove_guild_welcome_message(guild.id)
        logger.info(
            f"KoalaBot left guild, id = {guild.id}, name = {guild.name}. Removed {count} rows from GuildWelcomeMessages")

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.check(koalabot.is_admin)
    @commands.command(name="welcomeSendMsg", aliases=["send_welcome_message"])
    async def send_welcome_message(self, ctx):
        """
        Allows admins to send out their welcome message manually to all members of a guild. Has a 60 second cooldown per
        guild.

        :param ctx: Context of the command
        """
        non_bot_members = get_non_bot_members(ctx.guild)

        await ctx.send(f"This will DM {len(non_bot_members)} people. Are you sure you wish to do this? Y/N")
        try:
            confirmation_received = await ask_for_confirmation(await wait_for_message(self.bot, ctx), ctx.channel)
        except asyncio.TimeoutError:
            await ctx.send('Timed out.')
            confirmation_received = False
        if confirmation_received:
            await ctx.send("Okay, sending out the welcome message now.")
            await koalabot.dm_group_message(non_bot_members, get_guild_welcome_message(ctx.guild.id))
            return True
        else:
            await ctx.send("Okay, I won't send out the welcome message then.")
            return False

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.check(koalabot.is_admin)
    @commands.command(name="welcomeUpdateMsg", aliases=["update_welcome_message"])
    async def update_welcome_message(self, ctx, *, new_message: str):
        """
        Allows admins to change their customisable part of the welcome message of a guild. Has a 60 second cooldown per
        guild.

        :param ctx: Context of the command
        :param new_message: New customised part of the welcome message
        """
        if len(new_message) > 1600:
            await ctx.send("Your welcome message is too long to send, sorry. The maximum character limit is 1600.")
        else:
            await ctx.send(f"""Your current welcome message is:\n\r{get_guild_welcome_message(ctx.guild.id)}""")
            await ctx.send(f"""Your new welcome message will be:\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}\n\rWould """ +
                           """you like to update the message? Y/N?""")
            try:
                confirmation_received = await ask_for_confirmation(await wait_for_message(self.bot, ctx), ctx.channel)
            except asyncio.TimeoutError:
                await ctx.send('Timed out.')
                confirmation_received = False
            if confirmation_received:
                try:
                    await ctx.send("Okay, updating the welcome message of the guild in the database now.")
                    new_message = new_message.lstrip()
                    updated_entry = update_guild_welcome_message(ctx.guild.id, new_message)
                    await ctx.send(f"Updated in the database, your new welcome message is {updated_entry}.")
                except None:
                    await ctx.send("Something went wrong, please contact the bot developers for support.")
            else:
                await ctx.send("Okay, I won't update the welcome message then.")

    @commands.check(koalabot.is_admin)
    @commands.command(name="welcomeViewMsg")
    async def view_welcome_message(self, ctx):
        """
        Shows this server's current welcome message
        """
        await ctx.send(f"""Your current welcome message is:\n\r{get_guild_welcome_message(ctx.guild.id)}""")

    @update_welcome_message.error
    async def on_update_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.send('Please put in a welcome message to update to.')


async def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    await bot.add_cog(IntroCog(bot), override=True)
    logger.info("IntroCog is ready.")
