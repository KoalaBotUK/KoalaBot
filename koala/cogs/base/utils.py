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

# Variables


def new_discord_activity(activity, name):
    """
    This command takes an activity and name and returns the discord.Activity type for it

    Custom doesn't currently work
    koalabot.uk is added to the end of any activity
    :param activity: The new activity of the bot
    :param name: The name of the activity
    :return: The custom activity created
    """
    lower_activity = str.lower(activity)
    if lower_activity == "playing":
        activity_type = discord.ActivityType.playing
    elif lower_activity == "watching":
        activity_type = discord.ActivityType.watching
    elif lower_activity == "listening":
        activity_type = discord.ActivityType.listening
    elif lower_activity == "streaming":
        return discord.Activity(type=discord.ActivityType.streaming, name=name, url=koalabot.STREAMING_URL)
    elif lower_activity == "custom":
        return discord.Activity(type=discord.ActivityType.custom, name=name)
    else:
        raise SyntaxError(f"{activity} is not an activity")
    return discord.Activity(type=activity_type, name=name)


def list_ext_embed(guild_id):
    """
    Creates a discord embed of enabled and disabled extensions
    :param guild_id: The discord guild id of the server
    :return: The finished discord embed
    """
    embed = discord.Embed()
    embed.title = "Enabled extensions"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    enabled_results = get_enabled_guild_extensions(guild_id)
    all_results = get_all_available_guild_extensions(guild_id)
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
