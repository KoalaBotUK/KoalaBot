#!/usr/bin/env python

"""
Koala Bot Text Filter Code
Created by: Stefan Cooper
"""

# Built-in/Generic Imports
import re

import discord
# Libs
from discord.ext import commands

# Own modules
import koalabot
from koala.colours import KOALA_GREEN
from koala.db import insert_extension
from koala.log import logger
from koala.utils import extract_id
from .db import TextFilterDBManager
from . import core
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
        # self.tf_database_manager = TextFilterDBManager(bot)

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

        msg = core.filter_new_word(ctx.guild.id, word, filter_type, too_many_arguments)
        await ctx.send(msg)

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

        msg = core.filter_new_regex(ctx.guild.id, regex, filter_type, too_many_arguments)
        await ctx.send(msg)

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

        msg = core.unfilter_word(ctx.guild.id, word, too_many_arguments)
        await ctx.send(msg)

    @commands.command(name="filterList", aliases=["check_filtered_words", "checkFilteredWords"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def check_filtered_words(self, ctx):
        """
        Get a list of filtered words on the current guild.

        :param ctx: The discord context
        :return:
        """
        embed = core.get_filtered_words(ctx.guild.id)
        await ctx.channel.send(embed=embed)

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

        embed = core.setup_mod_channel(self.bot, ctx.guild.id, channel_id, too_many_arguments)
        await ctx.channel.send(embed=embed)

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

        embed = core.remove_mod_channel(self.bot, ctx.guild.id, channel_id, too_many_arguments)
        await ctx.channel.send(embed=embed)

    @commands.command(name="modChannelList", aliases=["list_mod_channels", "listModChannels"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def list_mod_channels(self, ctx):
        """
        Get a list of filtered mod channels in the guild

        :param ctx: The discord context
        :return:
        """
        await ctx.channel.send(embed=(core.list_mod_channels(self.bot, ctx.guild.id)))

    @commands.command(name="ignoreUser")
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def ignore_user(self, ctx, user):
        """
        Add a new ignored user to the database

        :param ctx: The discord context
        :param user: The discord mention of the User
        :return:
        """
        await ctx.channel.send(core.ignore_user(self.bot, ctx.guild.id, ctx.message.mentions[0].id, user))

    @commands.command(name="ignoreChannel")
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def ignore_channel(self, ctx, channel: discord.TextChannel):
        """
        Add a new ignored channel to the database

        :param ctx: The discord context
        :param channel: The discord mention of the Channel
        :return:
        """
        await ctx.channel.send(core.ignore_channel(self.bot, ctx.guild.id, channel))

    @commands.command(name="unignore", aliases=["remove_ignore", "removeIgnore"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def remove_ignore(self, ctx, ignore):
        """
        Remove an ignore from the guild

        :param ctx: The discord context
        :param ignore: the ignoreId to be removed
        :return:
        """
        await ctx.channel.send(core.remove_ignore(ctx.message.mentions, ctx.message.channel_mentions, ctx.guild.id, ignore))

    @commands.command(name="ignoreList", aliases=["list_ignored", "listIgnored"])
    @commands.check(koalabot.is_admin)
    @commands.check(text_filter_is_enabled)
    async def list_ignored(self, ctx):
        """
        Get a list all ignored users/channels

        :param ctx: The discord context
        :return:
        """
        await ctx.channel.send(embed=core.list_ignored(self.bot, ctx.guild.id))

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Upon receiving a message, it is checked for filtered text and is deleted.

        :param message: The newly received message
        :return:
        """
        result = core.scan_message(message)
        if result == "risky":
            await message.author.send("Watch your language! Your message: '*" + message.content + "*' in " +
                                                message.channel.mention + " contains a 'risky' word. "
                                                                        "This is a warning.")
        
        elif result == "banned":
            await message.author.send("Watch your language! Your message: '*" + message.content + "*' in " +
                                                message.channel.mention + " has been deleted by KoalaBot.")
            await core.send_to_moderation_channels(message)
            await message.delete()


async def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot

    :param  bot: The client of the KoalaBot
    """
    await bot.add_cog(TextFilter(bot))
