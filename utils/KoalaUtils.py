#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random

# Libs
import discord

# Own modules
from utils.KoalaColours import *

# Constants
ID_LENGTH = 18


# Variables


def random_id():
    """
    Creates a random int id of length ID_LENGTH
    :return: The randomly generated ID_LENGTH length number
    """
    range_start = 10**(ID_LENGTH-1)
    range_end = (10**ID_LENGTH)-1
    return random.randint(range_start, range_end)


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
        return raw_id
    else:
        raise TypeError("ID given is not a valid ID")
