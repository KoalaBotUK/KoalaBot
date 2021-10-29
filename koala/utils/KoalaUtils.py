#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import sys
import argparse
from pathlib import Path, PurePosixPath, PureWindowsPath

# Libs
from typing import Tuple, Optional
from pathlib import PurePath
import discord
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Own modules
from koala.utils.KoalaColours import ERROR_RED

# Constants
ID_LENGTH = 18
TIMEOUT_TIME = 60

# Variables
load_dotenv()

# Koala Constants
ENCRYPTED_DB = (not os.name == 'nt') and eval(os.environ.get('ENCRYPTED', "True"))
DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
CONFIG_PATH = os.getenv("CONFIG_PATH", "./config")
Base = declarative_base()
Session = sessionmaker(future=True)

DATABASE_PATH = None
engine = None
session = None

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


async def wait_for_message(bot: discord.Client, ctx: commands.Context, timeout: float = TIMEOUT_TIME) -> Tuple[
    Optional[discord.Message], Optional[discord.TextChannel]]:
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
    if config_dir and os.name == 'nt' and config_dir[1] != ":":
        config_dir = os.getcwd() + config_dir
    elif config_dir is None:
        config_dir = "./config"
    path = Path(config_dir)
    path.mkdir(exist_ok=True, parents=True)
    return str(path.absolute())


def _get_sql_url(db_path, encrypted: bool, db_key=None):
    if encrypted:
        return "sqlite+pysqlcipher://:x'" + db_key + "'@/" + db_path
    else:
        return "sqlite:///" + db_path


def set_variables(config):
    global CONFIG_DIR, DATABASE_PATH, engine, session

    CONFIG_DIR = config
    print("configDir: " + CONFIG_DIR)
    DATABASE_PATH = format_config_path(CONFIG_DIR, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")

    engine = create_engine(_get_sql_url(db_path=DATABASE_PATH,
                                        encrypted=ENCRYPTED_DB,
                                        db_key=DB_KEY), future=True)

    Session.configure(bind=engine)

    session = Session()


CONFIG_DIR = get_arg_config_path()

set_variables(CONFIG_DIR)
