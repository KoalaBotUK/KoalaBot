#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random

# Libs
from typing import Tuple, Optional

import discord

# Own modules
from discord.ext import commands

from utils.KoalaColours import *

# Constants
ID_LENGTH = 18
TIMEOUT_TIME = 60

# Variables


def random_id():
    """
    Creates a random int id of length ID_LENGTH
    :return: The randomly generated ID_LENGTH length number
    """
    range_start = 10 ** (ID_LENGTH - 1)
    range_end = (10 ** ID_LENGTH) - 1
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


def change_field_types(query_result: [[]], new_types: [type]):
    """
    Change the types within a query result

    :param query_result: The result from a db query
    :param new_types: A list of the new types to be assigned, must be the same length as the fields in query_result
    :return:
    """
    for i in range(len(query_result)):
        new_row = []
        for j in range(len(query_result[i])):
            if query_result[i][j]:
                new_row.append(new_types[j](query_result[i][j]))
            else:
                new_row.append(None)
        query_result[i] = tuple(new_row)
    return query_result
