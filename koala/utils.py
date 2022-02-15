#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import argparse
from pathlib import Path

# Libs
from typing import Tuple, Optional
from pathlib import PurePath
import discord
from discord.ext import commands

# Own modules
from koala.env import CONFIG_PATH
from koala.colours import ERROR_RED

# Constants
ID_LENGTH = 18
TIMEOUT_TIME = 60


# Variables

# Koala Constants


def error_embed(description, error_type=None):
    """
    Creates a discord embed for error messages
    :param description: The description of the error
    :param error_type: The error type (e.g. FileNotFoundError)
    :return: The completed embed
    """
    if isinstance(description, BaseException) and error_type is None:
        return discord.Embed(title=str(type(description).__name__), description=str(description), colour=ERROR_RED)
    elif error_type is None:
        return discord.Embed(title="Error", description=str(description), colour=ERROR_RED)
    else:
        return discord.Embed(title=error_type, description=str(description), colour=ERROR_RED)


def is_channel_in_guild(bot: discord.client, guild_id, channel_id):
    return bot.get_channel(int(channel_id)) in bot.get_guild(guild_id).channels


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def extract_id(raw_id):
    if type(raw_id) is str and raw_id[0] == "<":
        while not is_int(raw_id[0]):
            raw_id = raw_id[1:]
        return int(raw_id[:-1])
    elif is_int(raw_id):
        return int(raw_id)
    else:
        raise TypeError("ID given is not a valid ID")


async def wait_for_message(bot: discord.Client, ctx: commands.Context, timeout: float = TIMEOUT_TIME) \
        -> Tuple[Optional[discord.Message], Optional[discord.TextChannel]]:
    """
        Wraps bot.wait_for with message event, checking that message author is the original context author. Has default
        timeout of 60 seconds.
        :param bot: Koala Bot client
        :param ctx: Context of the original command
        :param timeout: Time to wait before raising TimeoutError
        :return: If a message (msg) was received, returns a tuple (msg, None). Else returns (None, ctx.channel)
        """
    try:
        msg = await bot.wait_for('message', timeout=timeout, check=lambda message: message.author == ctx.author)
    except (Exception, TypeError):
        return None, ctx.channel
    if not msg:
        return msg, ctx.channel
    return msg, None


def format_config_path(directory: str, *filename: str):
    """
    Format the path to be used by the database.

    This will be parsed directly into sqlite3 create connection.

    :param directory: The directory for the database file
    :param filename: The filename of the given database
    """
    if not directory:
        directory = ""

    return str(PurePath(directory, *filename))


def __parse_args(args):
    """
    Uses argparse to return a parser of all given arguments when running KoalaBot.py

    :param args: sys.argv[1:]
    :return: parsed argparse
    """
    parser = argparse.ArgumentParser(description='Start the KoalaBot Discord bot')
    parser.add_argument('--config', help="Config & database directory")
    args, unknown = parser.parse_known_args(args)
    return args


def get_arg_config_path():
    """
    Gets config directory if given from arguments when running KoalaBot.py

    :return: Valid config dir
    """
    config_dir = CONFIG_PATH
    if config_dir is None:
        config_dir = "./config"

    path = Path(config_dir)
    path.mkdir(exist_ok=True, parents=True)
    return str(path.absolute())
