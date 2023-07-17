#!/usr/bin/env python

"""
Koala Bot Text Filter Code
Created by: Stefan Cooper
"""

# Built-in/Generic Imports

# Libs
import discord

# Own modules
from koala.colours import KOALA_GREEN


def type_exists(filter_type):
    """
    Validates the inputted filter_type

    :param filter_type: The filter type to be checked
    :return: boolean checking if the filter type can be handled by the system, checks for risky, banned or email
    """
    return filter_type == "risky" or filter_type == "banned"


def build_moderation_channel_embed(guild_id, channel, action):
    """
    Builds a moderation embed which display some information about the mod channel being created/removed

    :param guild_id: the guild ID
    :param channel: The channel to be created/removed
    :param action: either "Added" or "Removed" to tell the user what happened to the mod channel
    :return embed: The moderation embed to be sent to the user
    """
    embed = create_default_embed(guild_id)
    embed.title = "Koala Moderation - Mod Channel " + action
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel ID", value=channel.id)
    return embed


def build_word_list_embed(guild_id, all_words, all_types, all_regex):
    """
    Builds the embed that is sent to list all the filtered words

    :param guild_id: the guild ID
    :param all_words: List of all the filtered words in the guild
    :param all_types: List of all the corresponding filter types for the words in the guild
    :param all_regex: List of all regex in the guild
    :return embed with information about the deleted message:
    """
    embed = create_default_embed(guild_id)
    embed.title = "Koala Moderation - Filtered Words"
    if not all_words and not all_types and not all_regex:
        embed.add_field(name="No words found", value="For more help with using the Text Filter try k!help TextFilter")
    else:
        embed.add_field(name="Banned Words", value=all_words)
        embed.add_field(name="Filter Types", value=all_types)
        embed.add_field(name="Is Regex?", value=all_regex)
    return embed


def create_default_embed(guild_id):
    """
    Creates a default embed that all embeds share

    :param guild_id: the guild ID
    :return embed with basic information which should be built upon:
    """
    embed = discord.Embed()
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    return embed


def build_moderation_deleted_embed(message):
    """
    Builds the embed that is sent after a message is deleted for containing a banned word

    :param message: the message object to be deleted
    :return embed with information about the deleted message:
    """
    embed = create_default_embed(message)
    embed.title = "Koala Moderation - Message Deleted"
    embed.add_field(name="Reason", value="Contained banned word")
    embed.add_field(name="User", value=message.author.mention)
    embed.add_field(name="Channel", value=message.channel.mention)
    embed.add_field(name="Message", value=message.content)
    embed.add_field(name="Timestamp", value=message.created_at)
    return embed
