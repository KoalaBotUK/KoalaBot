#!/usr/bin/env python

"""
Koala Bot Intro Message Cog Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot

# Constants

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


def get_non_bot_members(guild: discord.Guild):
    if KoalaBot.is_dpytest:
        return [member for member in guild.members if not member.bot and str(member) != KoalaBot.TEST_BOT_USER]
    else:
        return [member for member in guild.members if not member.bot]
