#!/usr/bin/env python

"""
Koala Bot Base Code
Run this to start the Bot

Commented using reStructuredText (reST)
"""
__author__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures

# Built-in/Generic Imports
import os

# Libs
from discord.ext import commands
from dotenv import load_dotenv

# Own modules

# Constants
load_dotenv()
BOT_TOKEN = os.environ['DISCORD_TOKEN']
BOT_OWNER = os.environ['BOT_OWNER']
COMMAND_PREFIX = "k!"
STREAMING_URL = "https://twitch.tv/jaydwee"
COGS_DIR = "cogs"
KOALA_PLUG = " koalabot.uk"  # Added to every presence change, do not alter
TEST_USER = "TestUser#0001"  # Test user for dpytest

# Variables
started = False
client = commands.Bot(command_prefix=COMMAND_PREFIX)


def is_owner(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(KoalaBot.is_owner)
    :param ctx: The context of the message
    :return: True if owner or test, False otherwise
    """
    return ctx.author.id == BOT_OWNER\
        or str(ctx.author) == TEST_USER  # For automated testing


def is_admin(ctx):
    """
    A command used to check if the user of a command is the admin, or the testing bot
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    return ctx.author.guild_permissions.administrator\
        or str(ctx.author) == TEST_USER  # For automated testing


def load_all_cogs():
    """
    Loads all cogs in COGS_DIR into the client
    """
    for filename in os.listdir(COGS_DIR):
        if filename.endswith('.py'):
            client.load_extension(COGS_DIR.replace("/", ".")+f'.{filename[:-3]}')


if __name__ == "__main__":  # pragma: no cover
    os.system("title " + "KoalaBot")
    load_all_cogs()
    # Starts bot using the given BOT_ID
    client.run(BOT_TOKEN)
