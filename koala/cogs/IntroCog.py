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
from dotenv import load_dotenv

# Own modules
import KoalaBot
from KoalaBot import database_manager as DBManager

# Constants

load_dotenv()
BASE_LEGAL_MESSAGE = """This server utilizes KoalaBot. In joining this server, you agree to the Terms & Conditions of 
KoalaBot and confirm you have read and understand our Privacy Policy. For legal documents relating to this, please view 
the following link: http://legal.koalabot.uk/"""
DEFAULT_WELCOME_MESSAGE = "Hello. This is a default welcome message because the guild that this came from did not configure a welcome message! Please see below."
# Variables


def wait_for_message(bot: discord.Client, ctx: commands.Context, timeout=60.0) -> (discord.Message, discord.TextChannel):
    try:
        confirmation = bot.wait_for('message', timeout=timeout, check=lambda message: message.author == ctx.author)
        return confirmation
    except Exception:
        confirmation = None
    return confirmation, ctx.channel


async def ask_for_confirmation(confirmation: discord.Message, channel: discord.TextChannel):
    if confirmation is None:
        await channel.send('Timed out.')
        return False
    else:
        channel = confirmation.channel
        x = await confirm_message(confirmation)
        if x is None:
            await channel.send('Invalid input, please redo the command.')
            return False
        return x


async def confirm_message(message: discord.Message):
    conf_message = message.content.rstrip().strip().lower()
    if conf_message not in ['y', 'n']:
        return
    else:
        if conf_message == 'y':
            return True
        else:
            return False


def get_guild_welcome_message(guild_id: int):
    """
    Retrieves a guild's customised welcome message from the database. Includes the basic legal message constant
    :param guild_id: ID of the guild
    :return: The particular guild's welcome message : str
    """
    msg = DBManager.fetch_guild_welcome_message(guild_id)
    if msg is None:
        msg = DBManager.new_guild_welcome_message(guild_id)
    return f"{msg}\r\n{BASE_LEGAL_MESSAGE}"


def get_non_bot_members(guild: discord.Guild):
    if KoalaBot.is_dpytest:
        return [member for member in guild.members if not member.bot and str(member) != KoalaBot.TEST_BOT_USER]
    else:
        return [member for member in guild.members if not member.bot]


class IntroCog(commands.Cog, name="KoalaBot"):
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
        DBManager.new_guild_welcome_message(guild.id)
        KoalaBot.logger.info(f"KoalaBot joined new guild, id = {guild.id}, name = {guild.name}.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        On member joining guild, send DM to member with welcome message.
        :param member: Member which just joined guild
        """
        await KoalaBot.dm_group_message([member], get_guild_welcome_message(member.guild.id))
        KoalaBot.logger.info(f"New member {member.name} joined guild id {member.guild.id}. Sent them welcome message.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        On bot leaving guild, remove the guild from the database of guild welcome messages
        :param guild: Guild KoalaBot just left
        """
        count = DBManager.remove_guild_welcome_message(guild.id)
        KoalaBot.logger.info(
            f"KoalaBot left guild, id = {guild.id}, name = {guild.name}. Removed {count} rows from GuildWelcomeMessages")

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.check(KoalaBot.is_admin)
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
            await KoalaBot.dm_group_message(non_bot_members, get_guild_welcome_message(ctx.guild.id))
            return True
        else:
            await ctx.send("Okay, I won't send out the welcome message then.")
            return False

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.check(KoalaBot.is_admin)
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
                    updated_entry = DBManager.update_guild_welcome_message(ctx.guild.id, new_message)
                    await ctx.send(f"Updated in the database, your new welcome message is {updated_entry}.")
                except None:
                    await ctx.send("Something went wrong, please contact the bot developers for support.")
            else:
                await ctx.send("Okay, I won't update the welcome message then.")

    @commands.check(KoalaBot.is_admin)
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


def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    bot.add_cog(IntroCog(bot))
    print("IntroCog is ready.")
