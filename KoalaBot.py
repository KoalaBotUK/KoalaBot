#!/usr/bin/env python

"""
Koala Bot Base Code
Run this to start the Bot

Commented using reStructuredText (reST)
"""
__author__ = "Jack Draper, Kieran Allinson, Viraj Shah," \
             " Anan Venkatesh, Harry Nelson, Robert Slawik, Rurda Malik, Stefan Cooper"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah",
               "Anan Venkatesh", "Harry Nelson", "Robert Slawik", "Rurda Malik", "Stefan Cooper"]
__license__ = "MIT License"
__version__ = "0.0.3"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures

# Built-in/Generic Imports
import os
import logging
import sys
import argparse

# Libs
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Own modules
from utils.KoalaDBManager import KoalaDBManager as DBManager
from utils.KoalaUtils import error_embed

# Constants
logging.basicConfig(filename='KoalaBot.log')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
load_dotenv()
BOT_TOKEN = os.environ['DISCORD_TOKEN']
BOT_OWNER = os.environ.get('BOT_OWNER')
DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
COMMAND_PREFIX = "k!"
STREAMING_URL = "https://twitch.tv/jaydwee"
COGS_DIR = "cogs"
KOALA_PLUG = " koalabot.uk"  # Added to every presence change, do not alter
TEST_USER = "TestUser#0001"  # Test user for dpytest
TEST_BOT_USER = "FakeApp#0001"  # Test bot user for dpytest
DATABASE_PATH = "Koala.db"
KOALA_GREEN = discord.Colour.from_rgb(0, 170, 110)
PERMISSION_ERROR_TEXT = "This guild does not have this extension enabled, go to http://koalabot.uk, " \
                        "or use `k!help enableExt` to enable it"
KOALA_IMAGE_URL = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"

# Variables


def parse_args(args):
    parser = argparse.ArgumentParser(description='Start the KoalaBot Discord bot')
    parser.add_argument('--config', help="Config & database directory")
    return parser.parse_args(args)


if __name__ == '__main__':
    config_dir = vars(parse_args(sys.argv[1:])).get("config")
else:
    config_dir = None

started = False
if discord.__version__ != "1.3.4":
    logging.info("Intents Enabled")
    intent = discord.Intents.default()
    intent.members = True
    intent.guilds = True
    intent.messages = True
    client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intent)
else:
    logging.info("discord.py v1.3.4: Intents Disabled")
    client = commands.Bot(command_prefix=COMMAND_PREFIX)
database_manager = DBManager(DATABASE_PATH, DB_KEY, config_dir)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger('discord')
is_dpytest = False



def is_owner(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(KoalaBot.is_owner)
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
    e.g. @commands.check(KoalaBot.is_admin)
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


def load_all_cogs():
    """
    Loads all cogs in COGS_DIR into the client
    """
    UNRELEASED = []

    for filename in os.listdir(COGS_DIR):
        if filename.endswith('.py') and filename not in UNRELEASED:
            client.load_extension(COGS_DIR.replace("/", ".") + f'.{filename[:-3]}')


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
    if (not database_manager.extension_enabled(ctx.message.guild.id, extension_id)) and (not is_dpytest):
        raise PermissionError(PERMISSION_ERROR_TEXT)
    return True


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=error_embed(description=error))
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(embed=error_embed(description=error.original))
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=error_embed(description=f"{ctx.author.mention}, this command is still on cooldown for "
                                                     f"{str(error.retry_after)}s."))
    else:
        await ctx.send(embed=error_embed(description=error))


if __name__ == "__main__":  # pragma: no cover
    os.system("title " + "KoalaBot")
    database_manager.create_base_tables()
    load_all_cogs()
    # Starts bot using the given BOT_ID
    client.run(BOT_TOKEN)
