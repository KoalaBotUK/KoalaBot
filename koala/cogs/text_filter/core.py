# Built-in/Generic Imports
import re

import discord
# Libs
from discord.ext import commands

# Own modules
import koalabot
from koala.colours import KOALA_GREEN
from koala.db import insert_extension
from koala.utils import extract_id
from .db import TextFilterDBManager
from .utils import type_exists, build_word_list_embed, build_moderation_channel_embed, \
    create_default_embed, build_moderation_deleted_embed

# unsure if passing this in is okay
tf_database_manager = TextFilterDBManager(koalabot)

# helper methods
def build_channel_list(bot: koalabot.KoalaBot, channels, embed):
    """
    Builds a list of mod channels and adds them to the embed

    :param channels: list of mod channels
    :param embed: The pre-existing embed to add the channel list fields to
    :return embed: the updated embed with the list of channels appended to
    """
    for channel in channels:
        details = bot.get_channel(int(channel[0]))
        if details is not None:
            embed.add_field(name="Name & Channel ID", value=details.mention + " " + str(details.id), inline=False)
        else:
            embed.add_field(name="Channel ID", value=channel[0], inline=False)
    return embed

def build_channel_list_embed(bot: koalabot.KoalaBot, guild_id, channels):
    """
    Builds the embed that is sent to list all the mod channels

    :param guild_id: the guild ID
    :param channels: List of channels in the guild
    :return embed with list of mod channels:
    """
    embed = create_default_embed(guild_id)
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    embed.title = "Koala Moderation - Mod Channels"
    embed = build_channel_list(bot, channels, embed)
    return embed

def is_ignored(message):
    """
    Checks if the user/channel should be ignored

    :param message: The newly received message
    :return boolean if should be ignored or not:
    """
    ignore_list_users = tf_database_manager.get_ignore_list_users(message.guild.id)
    ignore_list_channels = tf_database_manager.get_ignore_list_channels(message.guild.id)
    return message.channel.id in ignore_list_channels or message.author.id in ignore_list_users

def filter_text(guild_id, text, filter_type, is_regex):
    """
    Calls to the datbase to filter a word

    :param guild_id: the guild ID
    :param text: the word to be filtered
    :param filter_type: the filter_type of the word to be added
    :param is_regex: boolean of if the text is regex
    """
    tf_database_manager.new_filtered_text(guild_id, text, filter_type, is_regex)

def unfilter(guild_id, word):
    """
    Calls to the database to unfilter a word

    :param guild_id: the guild ID
    :param word: The word to be unfiltered
    """
    tf_database_manager.remove_filter_text(guild_id, word)

def is_moderation_channel_available(guild_id):
    """
    Checks if any mod channels exist to be sent to

    :param guild_id: The guild to retrieve mod channels from
    :return: boolean true if mod channel exists, false otherwise
    """
    channels = tf_database_manager.get_mod_channel(guild_id)
    return len(channels) > 0

async def send_to_moderation_channels(bot: koalabot.KoalaBot, message):
    """
    Send details about deleted message to mod channels

    :param message: The message in question which is being deleted
    """
    if is_moderation_channel_available(message.guild.id):
        channels = tf_database_manager.get_mod_channel(message.guild.id)
        for each_channel in channels:
            channel = bot.get_channel(int(each_channel[0]))
            await channel.send(embed=build_moderation_deleted_embed(message))

def get_list_of_words(guild_id):
    """
    Gets a list of filtered words and corresponding types in a guild

    :param guild_id: the guild ID
    :return [all_words, all_types]: a list containing two lists of filtered words and types
    """
    all_words, all_types, all_regex = "", "", ""
    for word, filter_type, regex in tf_database_manager.get_filtered_text_for_guild(guild_id):
        all_words += word + "\n"
        all_types += filter_type + "\n"
        all_regex += regex + "\n"
    return [all_words, all_types, all_regex]

def build_ignore_list(bot: koalabot.KoalaBot, ignored, embed):
    """
    Builds a formatted list of ignored users/channels

    :param ignored: list of ignored users/channels
    :param embed: The pre-existing embed to add the channel list fields to
    :return embed: the updated embed with the list of channels appended to
    """
    for ig in ignored:
        if ig[2] == 'channel':
            details = bot.get_channel(int(ig[3]))
        else:
            details = bot.get_user(int(ig[3]))
        if details is not None:
            embed.add_field(name="Name & ID", value=details.mention + " " + str(details.id), inline=False)
        else:
            embed.add_field(name="ID", value=ig[3], inline=False)
    return embed

def build_ignore_list_embed(bot: koalabot.KoalaBot, guild_id, channels):
    """
    Builds the embed to list all ignored

    :param guild_id: the guild ID
    :param channels: List of ignored users/channels
    :return embed with list of mod channels:
    """
    embed = create_default_embed(guild_id)
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    embed.title = "Koala Moderation - Ignored Users/Channels"
    embed = build_ignore_list(bot, channels, embed)
    return embed


# logic methods

def filter_new_word(guild_id, word, filter_type, too_many_arguments):
    if too_many_arguments is None and type_exists(filter_type):
        filter_text(guild_id, word, filter_type, False)
        return ("*" + word + "* has been filtered as **" + filter_type + "**.")
    raise Exception("""Something has gone wrong, your word may already be filtered or you have entered the 
                command incorrectly. Try again with: `k!filter [filtered_text] [[risky] or [banned]]`""")


def filter_new_regex(guild_id, regex, filter_type, too_many_arguments):
    if too_many_arguments and type_exists(filter_type):
        try:
            re.compile(regex)
            filter_text(guild_id, regex, filter_type, True)
            return ("*" + regex + "* has been filtered as **" + filter_type + "**.")
        except:
            raise Exception(r"""Something has gone wrong, your regex may be invalid, this regex may already be filtered
                    or you have entered the command incorrectly. Try again with: `k!filterRegex 
                    [filtered_regex] [[risky] or [banned]]`. One example for a regex could be to block emails
                    with: [a-zA-Z0-9\._]+@herts\.ac\.uk where EMAIL is the university type (e.g herts)""")
    elif too_many_arguments:
        raise Exception("type doesn't exist")
    else:
        raise Exception("too many arguments")
    

def unfilter_word(guild_id, word, too_many_arguments):
    if too_many_arguments is None:
        unfilter(guild_id, word)
        return ("*" + word + "* has been unfiltered.")
    raise Exception("Too many arguments, please try again using the following arguments: `k!unfilter [filtered_word]`")


def get_filtered_words(guild_id):
    all_words_and_types = get_list_of_words(guild_id)
    return build_word_list_embed(guild_id, all_words_and_types[0],
                                all_words_and_types[1],
                                all_words_and_types[2])


def setup_mod_channel(bot: koalabot.KoalaBot, guild_id, channel_id, too_many_arguments):
    channel = bot.get_channel(int(extract_id(channel_id)))
    if channel is not None and too_many_arguments is None:
        tf_database_manager.new_mod_channel(guild_id, channel.id)
        return build_moderation_channel_embed(guild_id, channel, "Added")
    raise Exception("Channel not found or too many arguments, please try again: `k!setupModChannel [channel_id]`")


def remove_mod_channel(bot: koalabot.KoalaBot, guild_id, channel_id, too_many_arguments):
    channel = bot.get_channel(int(extract_id(channel_id)))
    if channel is not None and too_many_arguments is None:
        tf_database_manager.remove_mod_channel(guild_id, channel_id)
        return build_moderation_channel_embed(guild_id, channel, "Removed")
    raise Exception("""Missing Channel ID or too many arguments remove a mod channel. If you don't know your Channel ID,
                use `k!listModChannels` to get information on your mod channels.""")


def list_mod_channels(bot: koalabot.KoalaBot, guild_id):
    channels = tf_database_manager.get_mod_channel(guild_id)
    return build_channel_list_embed(bot, guild_id, channels)


def ignore_user(bot: koalabot.KoalaBot, guild_id, ignore_id, user):
    ignore_exists = bot.get_user(int(ignore_id))
    if ignore_exists is not None:
        tf_database_manager.new_ignore(guild_id, 'user', ignore_id)
        return ("New ignore added: " + user)
    raise Exception("""Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID,
            use `k!listModChannels` to get information on your mod channels.""")


def ignore_channel(bot: koalabot.KoalaBot, guild_id, channel):
    ignore_exists = bot.get_channel(int(channel.id))
    if ignore_exists is not None:
        tf_database_manager.new_ignore(guild_id, 'channel', channel.id)
        return f"New ignore added: {channel.mention}"
    raise Exception("""Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID, 
            use `k!listModChannels` to get information on your mod channels.""")


def remove_ignore(msg_mentions, channel_mentions, guild_id, ignore):
    if len(msg_mentions) > 0:
        ignore_id = msg_mentions[0].id
    elif len(channel_mentions) > 0:
        ignore_id = channel_mentions[0].id
    else:
        raise Exception("No ignore mention found")
    tf_database_manager.remove_ignore(guild_id, ignore_id)
    return ("Ignore removed: " + str(ignore))


def list_ignored(bot: koalabot.KoalaBot, guild_id):
    ignored = tf_database_manager.get_all_ignored(guild_id)
    return build_ignore_list_embed(bot, guild_id, ignored)


def scan_message(message):
    if message.author.bot:
        return
    if message.content.startswith(koalabot.COMMAND_PREFIX + "filter") or \
            message.content.startswith(koalabot.COMMAND_PREFIX + "unfilter") or \
            message.content.startswith(koalabot.OPT_COMMAND_PREFIX + "filter") or \
            message.content.startswith(koalabot.OPT_COMMAND_PREFIX + "unfilter"):
        return
    elif str(message.channel.type) == 'text' and message.channel.guild is not None:
        censor_list = tf_database_manager.get_filtered_text_for_guild(message.channel.guild.id)
        for word, filter_type, is_regex in censor_list:
            if (word in message.content or (
                    is_regex == '1' and re.search(word, message.content))) and not is_ignored(message):
                return filter_type