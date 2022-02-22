#!/usr/bin/env python

"""
Koala Bot Text Filter Code
Created by: Stefan Cooper
"""

# Built-in/Generic Imports
import re

# Libs
from discord.ext import commands

# Own modules
import koalabot
from koala.db import insert_extension
from koala.colours import KOALA_GREEN
from koala.utils import extract_id

from .db import TextFilterDBManager
from .utils import type_exists, build_word_list_embed, build_moderation_channel_embed, \
    create_default_embed, build_moderation_deleted_embed


def text_filter_is_enabled(ctx):
    """
    A command used to check if the guild has enabled TextFilter
    e.g. @commands.check(koalabot.is_admin)

    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(ctx, "TextFilter")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == koalabot.TEST_USER and koalabot.is_dpytest)


class TextFilter(commands.Cog, name="TextFilter"):
    """
    A discord.py cog with commands pertaining to the a Text Filter for admins to monitor their server
    """

    def __init__(self, bot):
        self.bot = bot
        insert_extension("TextFilter", 0, True, True)
        self.tf_database_manager = TextFilterDBManager(bot)

    @commands.command(name="filter", aliases=["filter_word"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def filter_new_word(self, ctx, word, filter_type="banned", too_many_arguments=None):
        """
        Adds a new word to the filtered text list

        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :param filter_type: The filter type (banned or risky)
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = """Something has gone wrong, your word may already be filtered or you have entered the 
                command incorrectly. Try again with: `k!filter [filtered_text] [[risky] or [banned]]`"""
        if too_many_arguments is None and type_exists(filter_type):
            await self.filter_text(ctx, word, filter_type, False)
            await ctx.channel.send("*" + word + "* has been filtered as **" + filter_type + "**.")
            return
        raise Exception(error)

    @commands.command(name="filterRegex", aliases=["filter_regex"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def filter_new_regex(self, ctx, regex, filter_type="banned", too_many_arguments=None):
        """
        Adds a new regex to the filtered text list

        :param ctx: The discord context
        :param regex: The first argument and regex to be filtered
        :param filter_type: The filter type (banned or risky)
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = r"""Something has gone wrong, your regex may be invalid, this regex may already be filtered
                or you have entered the command incorrectly. Try again with: `k!filterRegex 
                [filtered_regex] [[risky] or [banned]]`. One example for a regex could be to block emails
                with: [a-zA-Z0-9\._]+@herts\.ac\.uk where EMAIL is the university type (e.g herts)"""
        if too_many_arguments is None and type_exists(filter_type):
            try:
                re.compile(regex)
                await self.filter_text(ctx, regex, filter_type, True)
                await ctx.channel.send("*" + regex + "* has been filtered as **" + filter_type + "**.")
                return
            except:
                raise Exception(error)
        raise Exception(error)

    @commands.command(name="unfilter", aliases=["unfilter_word"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def unfilter_word(self, ctx, word, too_many_arguments=None):
        """
        Remove an existing word/test from the filter list

        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = "Too many arguments, please try again using the following arguments: `k!unfilter [filtered_word]`"
        if too_many_arguments is None:
            await self.unfilter_text(ctx, word)
            await ctx.channel.send("*" + word + "* has been unfiltered.")
            return
        raise Exception(error)

    @commands.command(name="filterList", aliases=["check_filtered_words", "checkFilteredWords"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def check_filtered_words(self, ctx):
        """
        Get a list of filtered words on the current guild.

        :param ctx: The discord context
        :return:
        """
        all_words_and_types = self.get_list_of_words(ctx)
        await ctx.channel.send(embed=build_word_list_embed(ctx, all_words_and_types[0], all_words_and_types[1],
                                                           all_words_and_types[2]))

    @commands.command(name="modChannelAdd", aliases=["setup_mod_channel", "setupModChannel",
                                                     "add_mod_channel", "addModChannel"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def setup_mod_channel(self, ctx, channel_id, too_many_arguments=None):
        """
        Add a mod channel to the current guild

        :param ctx: The discord context
        :param channel_id: The designated channel id for message details
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = "Channel not found or too many arguments, please try again: `k!setupModChannel [channel_id]`"
        channel = self.bot.get_channel(int(extract_id(channel_id)))
        if channel is not None and too_many_arguments is None:
            self.tf_database_manager.new_mod_channel(ctx.guild.id, channel.id)
            await ctx.channel.send(embed=build_moderation_channel_embed(ctx, channel, "Added"))
            return
        raise (Exception(error))

    @commands.command(name="modChannelRemove", aliases=["remove_mod_channel", "deleteModChannel", "removeModChannel"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def remove_mod_channel(self, ctx, channel_id, too_many_arguments=None):
        """
        Remove a mod channel from the guild

        :param ctx: The discord context
        :param channel_id: The designated channel id to be removed
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = """Missing Channel ID or too many arguments remove a mod channel. If you don't know your Channel ID,
                use `k!listModChannels` to get information on your mod channels."""
        channel = self.bot.get_channel(int(extract_id(channel_id)))
        if channel is not None and too_many_arguments is None:
            self.tf_database_manager.remove_mod_channel(ctx.guild.id, channel_id)
            await ctx.channel.send(embed=build_moderation_channel_embed(ctx, channel, "Removed"))
            return
        raise Exception(error)

    @commands.command(name="modChannelList", aliases=["list_mod_channels", "listModChannels"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def list_mod_channels(self, ctx):
        """
        Get a list of filtered mod channels in the guild

        :param ctx: The discord context
        :return:
        """
        channels = self.tf_database_manager.get_mod_channel(ctx.guild.id)
        await ctx.channel.send(embed=self.build_channel_list_embed(ctx, channels))

    @commands.command(name="ignoreUser")
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def ignore_user(self, ctx, user, too_many_arguments=None):
        """
        Add a new ignored user to the database

        :param ctx: The discord context
        :param user: The discord mention of the User
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = """Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID,
                use `k!listModChannels` to get information on your mod channels."""
        ignore_id = ctx.message.mentions[0].id
        ignore_exists = self.bot.get_user(int(ignore_id))
        if ignore_exists is not None:
            self.tf_database_manager.new_ignore(ctx.guild.id, 'user', ignore_id)
            await ctx.channel.send("New ignore added: " + user)
            return
        raise (Exception(error))

    @commands.command(name="ignoreChannel")
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def ignore_channel(self, ctx, channel, too_many_arguments=None):
        """
        Add a new ignored channel to the database

        :param ctx: The discord context
        :param channel: The discord mention of the Channel
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        error = """Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID, 
                use `k!listModChannels` to get information on your mod channels."""
        ignore_id = ctx.message.channel_mentions[0].id
        ignore_exists = self.bot.get_channel(int(ignore_id))
        if ignore_exists is not None:
            self.tf_database_manager.new_ignore(ctx.guild.id, 'channel', ignore_id)
            await ctx.channel.send("New ignore added: " + channel)
            return
        raise (Exception(error))

    @commands.command(name="unignore", aliases=["remove_ignore", "removeIgnore"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def remove_ignore(self, ctx, ignore, too_many_arguments=None):
        """
        Remove an ignore from the guild

        :param ctx: The discord context
        :param ignore: the ignoreId to be removed
        :param too_many_arguments: Used to check if too many arguments have been given
        :return:
        """
        if len(ctx.message.mentions) > 0:
            ignore_id = ctx.message.mentions[0].id
        elif len(ctx.message.channel_mentions) > 0:
            ignore_id = ctx.message.channel_mentions[0].id
        else:
            raise Exception("No ignore mention found")
        self.tf_database_manager.remove_ignore(ctx.guild.id, ignore_id)
        await ctx.channel.send("Ignore removed: " + str(ignore))
        return

    @commands.command(name="ignoreList", aliases=["list_ignored", "listIgnored"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def list_ignored(self, ctx):
        """
        Get a list all ignored users/channels

        :param ctx: The discord context
        :return:
        """
        ignored = self.tf_database_manager.get_all_ignored(ctx.guild.id)
        await ctx.channel.send(embed=self.build_ignore_list_embed(ctx, ignored))

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Upon receiving a message, it is checked for filtered text and is deleted.

        :param message: The newly received message
        :return:
        """
        if message.author.bot:
            return
        if message.content.startswith(koalabot.COMMAND_PREFIX + "filter") or \
                message.content.startswith(koalabot.COMMAND_PREFIX + "unfilter") or \
                message.content.startswith(koalabot.OPT_COMMAND_PREFIX + "filter") or \
                message.content.startswith(koalabot.OPT_COMMAND_PREFIX + "unfilter"):
            return
        elif str(message.channel.type) == 'text' and message.channel.guild is not None:
            censor_list = self.tf_database_manager.get_filtered_text_for_guild(message.channel.guild.id)
            for word, filter_type, is_regex in censor_list:
                if (word in message.content or (
                        is_regex == '1' and re.search(word, message.content))) and not self.is_ignored(message):
                    if filter_type == "risky":
                        await message.author.send("Watch your language! Your message: '*" + message.content + "*' in " +
                                                  message.channel.mention + " contains a 'risky' word. "
                                                                            "This is a warning.")
                        return
                    elif filter_type == "banned":
                        await message.author.send("Watch your language! Your message: '*" + message.content + "*' in " +
                                                  message.channel.mention + " has been deleted by KoalaBot.")
                        await self.send_to_moderation_channels(message)
                        await message.delete()
                        return

    def build_channel_list(self, channels, embed):
        """
        Builds a list of mod channels and adds them to the embed

        :param channels: list of mod channels
        :param embed: The pre-existing embed to add the channel list fields to
        :return embed: the updated embed with the list of channels appended to
        """
        for channel in channels:
            details = self.bot.get_channel(int(channel[0]))
            if details is not None:
                embed.add_field(name="Name & Channel ID", value=details.mention + " " + str(details.id), inline=False)
            else:
                embed.add_field(name="Channel ID", value=channel[0], inline=False)
        return embed

    def build_channel_list_embed(self, ctx, channels):
        """
        Builds the embed that is sent to list all the mod channels

        :param ctx: The discord context
        :param channels: List of channels in the guild
        :return embed with list of mod channels:
        """
        embed = create_default_embed(ctx)
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        embed.title = "Koala Moderation - Mod Channels"
        embed = self.build_channel_list(channels, embed)
        return embed

    def is_ignored(self, message):
        """
        Checks if the user/channel should be ignored

        :param message: The newly received message
        :return boolean if should be ignored or not:
        """
        ignore_list_users = self.tf_database_manager.get_ignore_list_users(message.guild.id)
        ignore_list_channels = self.tf_database_manager.get_ignore_list_channels(message.guild.id)
        return message.channel.id in ignore_list_channels or message.author.id in ignore_list_users

    async def filter_text(self, ctx, text, filter_type, is_regex):
        """
        Calls to the datbase to filter a word

        :param ctx: the discord context
        :param text: the word to be filtered
        :param filter_type: the filter_type of the word to be added
        :param is_regex: boolean of if the text is regex
        """
        self.tf_database_manager.new_filtered_text(ctx.guild.id, text, filter_type, is_regex)

    async def unfilter_text(self, ctx, word):
        """
        Calls to the database to unfilter a word

        :param ctx: The discord context
        :param word: The word to be unfiltered
        """
        self.tf_database_manager.remove_filter_text(ctx.guild.id, word)

    def is_moderation_channel_available(self, guild_id):
        """
        Checks if any mod channels exist to be sent to

        :param guild_id: The guild to retrieve mod channels from
        :return: boolean true if mod channel exists, false otherwise
        """
        channels = self.tf_database_manager.get_mod_channel(guild_id)
        return len(channels) > 0

    async def send_to_moderation_channels(self, message):
        """
        Send details about deleted message to mod channels

        :param message: The message in question which is being deleted
        """
        if self.is_moderation_channel_available(message.guild.id):
            channels = self.tf_database_manager.get_mod_channel(message.guild.id)
            for each_channel in channels:
                channel = self.bot.get_channel(id=int(each_channel[0]))
                await channel.send(embed=build_moderation_deleted_embed(message))

    def get_list_of_words(self, ctx):
        """
        Gets a list of filtered words and corresponding types in a guild

        :param ctx: the discord context
        :return [all_words, all_types]: a list containing two lists of filtered words and types
        """
        all_words, all_types, all_regex = "", "", ""
        for word, filter_type, regex in self.tf_database_manager.get_filtered_text_for_guild(ctx.guild.id):
            all_words += word + "\n"
            all_types += filter_type + "\n"
            all_regex += regex + "\n"
        return [all_words, all_types, all_regex]

    def build_ignore_list(self, ignored, embed):
        """
        Builds a formatted list of ignored users/channels

        :param ignored: list of ignored users/channels
        :param embed: The pre-existing embed to add the channel list fields to
        :return embed: the updated embed with the list of channels appended to
        """
        for ig in ignored:
            if ig[2] == 'channel':
                details = self.bot.get_channel(int(ig[3]))
            else:
                details = self.bot.get_user(int(ig[3]))
            if details is not None:
                embed.add_field(name="Name & ID", value=details.mention + " " + str(details.id), inline=False)
            else:
                embed.add_field(name="ID", value=ig[3], inline=False)
        return embed

    def build_ignore_list_embed(self, ctx, channels):
        """
        Builds the embed to list all ignored

        :param ctx: The discord context
        :param channels: List of ignored users/channels
        :return embed with list of mod channels:
        """
        embed = create_default_embed(ctx)
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        embed.title = "Koala Moderation - Ignored Users/Channels"
        embed = self.build_ignore_list(channels, embed)
        return embed


def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot

    :param  bot: The client of the KoalaBot
    """
    bot.add_cog(TextFilter(bot))
