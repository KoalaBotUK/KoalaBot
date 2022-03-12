#!/usr/bin/env python

"""
Koala Bot Base Code
Run this to start the Bot

Commented using reStructuredText (reST)
"""
__author__ = "KoalaBotUK"
__copyright__ = "Copyright (c) 2020 KoalaBotUK"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah", "Stefan Cooper", "Anan Venkatesh", "Harry Nelson",
               "Bill Cao", "Aqeel Little", "Charlie Bowe", "Ponmile Femi-Sunmaila",
               "see full list of developers at: https://koalabot.uk/"]
__license__ = "MIT License"
__version__ = "0.4.5"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah, Stefan Cooper, Otto Hooper"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures
# Built-in/Generic Imports
import os
import time

# Libs
import discord
from discord.ext import commands
from dotenv import load_dotenv
import importlib
from flask import Flask
from threading import Thread
from functools import partial

# Own modules
from koala.db import extension_enabled
from koala.utils import error_embed
from koala.log import logger
from koala.env import BOT_TOKEN, BOT_OWNER

# Flask
flask_app = Flask(__name__)

# Constants
load_dotenv()

COMMAND_PREFIX = "k!"
OPT_COMMAND_PREFIX = "K!"
STREAMING_URL = "https://twitch.tv/jaydwee"
COGS_DIR = "koala/cogs"
KOALA_PLUG = " koalabot.uk"  # Added to every presence change, do not alter
TEST_USER = "TestUser#0001"  # Test user for dpytest
TEST_BOT_USER = "FakeApp#0001"  # Test bot user for dpytest
KOALA_GREEN = discord.Colour.from_rgb(0, 170, 110)
PERMISSION_ERROR_TEXT = "This guild does not have this extension enabled, go to http://koalabot.uk, " \
                        "or use `k!help enableExt` to enable it"
KOALA_IMAGE_URL = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"
ENABLED_COGS = ["base", "announce", "colour_role", "intro_cog", "react_for_role", "text_filter", "twitch_alert",
                "verification", "voting"]

# Variables
started = False
intent = discord.Intents.default()
intent.members = True
intent.guilds = True
intent.messages = True
client = commands.Bot(command_prefix=[COMMAND_PREFIX, OPT_COMMAND_PREFIX], intents=intent)
is_dpytest = False

def is_owner(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(koalabot.is_owner)
    :param ctx: The context of the message
    :return: True if owner or test, False otherwise
    """
    if is_dm_channel(ctx):
        return False
    elif BOT_OWNER is not None:
        return ctx.author.id == int(BOT_OWNER) or is_dpytest
    else:
        return client.is_owner(ctx.author) or is_dpytest


def is_admin(ctx):
    """
    A command used to check if the user of a command is the admin, or the testing bot
    e.g. @commands.check(koalabot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    if is_dm_channel(ctx):
        return False
    else:
        return ctx.author.guild_permissions.administrator or is_dpytest


def is_dm_channel(ctx):
    return isinstance(ctx.channel, discord.channel.DMChannel)


def is_guild_channel(ctx):
    return ctx.guild is not None

def load_apis():
    for cog in ENABLED_COGS:
        module_name = 'koala.cogs.'+cog+'.cog'
        print(module_name)
        try:
            # flask_app.register_blueprint(getimportlib.import_module(module_name))
            flask_app.register_blueprint(getattr(importlib.import_module(module_name), cog + '_api'))
        except commands.errors.ExtensionAlreadyLoaded:
            print("API already loaded")

def load_all_cogs():
    """
    Loads all cogs in COGS_DIR into the client
    """
    UNRELEASED = []

    for filename in os.listdir(COGS_DIR):
        if filename.endswith('.py') and filename not in UNRELEASED and filename != "__init__.py":
            try:
                client.load_extension(COGS_DIR.replace("/", ".") + f'.{filename[:-3]}')
            except commands.errors.ExtensionAlreadyLoaded:
                client.reload_extension(COGS_DIR.replace("/", ".") + f'.{filename[:-3]}')

    # New Approach
    for cog in ENABLED_COGS:
        module_name = 'koala.cogs.'+cog+'.cog'
        try:
            client.load_extension(module_name)
        except commands.errors.ExtensionAlreadyLoaded:
            client.reload_extension(module_name)

    logger.info("All cogs loaded")


def get_channel_from_id(id):
    return client.get_channel(id=id)


async def dm_group_message(members: [discord.Member], message: str):
    """
    DMs members in a list of members
    :param members: list of members to DM
    :param message: The message to send to the group
    :return: how many were dm'ed successfully.
    """
    count = 0
    for member in members:
        try:
            await member.send(message)
            count = count + 1
        except Exception:  # In case of user dms being closed
            pass
    return count


def check_guild_has_ext(ctx, extension_id):
    """
    A check for if a guild has a given koala extension
    :param ctx: A discord context
    :param extension_id: The koala extension ID
    :return: True if has ext
    """
    if is_dm_channel(ctx):
        return False
    if (not extension_enabled(ctx.message.guild.id, extension_id)) and (not is_dpytest):
        raise PermissionError(PERMISSION_ERROR_TEXT)
    return True


@client.event
async def on_command_error(ctx, error: Exception):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=error_embed(description=error))
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=error_embed(description=f"{ctx.author.mention}, this command is still on cooldown for "
                                                     f"{str(error.retry_after)}s."))
    elif isinstance(error, commands.errors.ChannelNotFound):
        await ctx.send(embed=error_embed(description=f"The channel ID provided is either invalid, or not in this server."))
    elif isinstance(error, commands.CommandInvokeError):
        # logger.warning("CommandInvokeError(%s), guild_id: %s, message: %s", error.original, ctx.guild.id, ctx.message)
        await ctx.send(embed=error_embed(description=error.original))
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(embed=error_embed(description=error))
    else:
        logger.error(f"Unexpected Error in guild {ctx.guild.name}: {error}")
        await ctx.send(embed=error_embed(
            description=f"An unexpected error occurred, please contact an administrator Timestamp: {time.time()}")) # FIXME: better timestamp
        raise error

# load_apis()
if __name__ == "__main__":  # pragma: no cover
    os.system("title " + "KoalaBot")
    load_all_cogs()
    load_apis()

    # Run Flask in seperate thread
    flask_run = partial(flask_app.run, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    flask_thread = Thread(target=flask_run)
    flask_thread.start()

    # Starts bot using the given BOT_ID
    client.run(BOT_TOKEN)

    
