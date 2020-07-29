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


def error_embed(description, error_type="Error"):
    """
    Creates a discord embed for error messages
    :param description: The description of the error
    :param error_type: The error type (e.g. FileNotFoundError)
    :return: The completed embed
    """
    return discord.Embed(title=f"{error_type}: {description}", colour=ERROR_RED)


def is_channel_in_guild(bot: discord.client, guild_id, channel_id):
    return bot.get_channel(int(channel_id)) in bot.get_guild(guild_id).channels
