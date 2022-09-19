#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord

# Own modules
import koalabot
from koala.db import get_enabled_guild_extensions, get_all_available_guild_extensions
from koala.colours import KOALA_GREEN


# Constants
DEFAULT_ACTIVITY = discord.Activity(type=discord.ActivityType.playing, name=f"{koalabot.COMMAND_PREFIX}help koalabot.uk")
AUTO_UPDATE_ACTIVITY_DELAY = 1
# Variables


def list_ext_embed(guild_id, **kwargs):
    """
    Creates a discord embed of enabled and disabled extensions
    :param guild_id: The discord guild id of the server
    :return: The finished discord embed
    """
    embed = discord.Embed()
    embed.title = "Enabled extensions"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    enabled_results = get_enabled_guild_extensions(guild_id, **kwargs)
    all_results = get_all_available_guild_extensions(guild_id, **kwargs)
    enabled = ""
    disabled = ""
    for result in enabled_results:
        enabled += f"{result}\n"
        try:
            all_results.remove(result)
        except ValueError:
            pass
    for result in all_results:
        disabled += f"{result}\n"
    if enabled != "":
        embed.add_field(name=":white_check_mark: Enabled", value=enabled)
    if disabled != "":
        embed.add_field(name=":negative_squared_cross_mark: Disabled", value=disabled)
    return embed


def activity_eq(activity1: discord.Activity, activity2: discord.Activity) -> bool:
    return activity1 and activity2 \
           and activity1.type == activity2.type \
           and activity1.name == activity2.name \
           and activity1.url == activity2.url
