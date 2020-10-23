#!/usr/bin/env python

"""
Koala Bot Text Filter Code
"""

# Built-in/Generic Imports
import os
import asyncio
import time
import re
import aiohttp
import logging

# Libs
from discord.ext import commands, tasks
from dotenv import load_dotenv
if os.name == 'nt':
    logging.info("Windows Detected: Database Encryption Disabled")
    import sqlite3
else:
    logging.info("Linux Detected: Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

# Own modules
import KoalaBot
from utils.KoalaColours import *
from utils.KoalaUtils import error_embed, is_channel_in_guild, extract_id
from utils.KoalaDBManager import KoalaDBManager

if os.name == 'nt':
    logging.info("Windows Detected: Database Encryption Disabled")
    import sqlite3
else:
    logging.info("Linux Detected: Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

# Constants
load_dotenv()

class TextFilterCog(commands.Cog):
    """
    A discord.py cog with commands pertaining to the a Text Filter for admins to monitor their server
    """

    def __init__(self, bot, database_manager=None):
        if not database_manager:
            database_manager = KoalaBot.database_manager
        self.bot = bot
        database_manager.create_base_tables()
        database_manager.insert_extension("TextFilter", 0, True, True)
        self.tf_database_manager = TextFilterDBManager(database_manager, bot)
        self.tf_database_manager.create_tables()

    @commands.command(name="filter", aliases=["filter_word"])
    @commands.check(KoalaBot.is_admin)
    async def filter_new_word(self, ctx, word, filter_type="banned", too_many_arguments=None):
        """
        Adds new word to the filtered text list
        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :param filter_type: The filter type (banned or risky)
        :return:
        """
        error = "Something has gone wrong, your word may already be filtered or you have entered the command incorrectly. You try again with: `k!filter [filtered_text] [[risky] or [banned]]`"
        if too_many_arguments == None and typeExists(filter_type):
            await filterText(self, ctx, word, filter_type, False)
            await ctx.channel.send("*" + word + "* has been filtered as **"+filter_type+"**.")
            return
        raise Exception(error)

    @commands.command(name="filterRegex", aliases=["filter_regex"])
    @commands.check(KoalaBot.is_admin)
    async def filter_new_regex(self, ctx, regex, filter_type="banned", too_many_arguments=None):
        """
        Adds new word to the filtered text list
        :param ctx: The discord context
        :param regex: The first argument and regex to be filtered
        :param filter_type: The filter type (banned or risky)
        :return:
        """
        error = "Something has gone wrong, this regex may already be filtered or you have entered the command incorrectly. You try again with: `k!filterRegex [filtered_regex] [[risky] or [banned]]`. \
                One example for a regex could be to block emails with: [a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk] where EMAIL is the university type (e.g herts)"
        if too_many_arguments == None and typeExists(filter_type):
            await filterText(self, ctx, regex, filter_type, True)
            await ctx.channel.send("*" + regex + "* has been filtered as **"+filter_type+"**.")
            return
        raise Exception(error)

    @commands.command(name="unfilter", aliases=["unfilter_word"])
    @commands.check(KoalaBot.is_admin)
    async def unfilter_word(self, ctx, word, too_many_arguments=None):
        """
        Removes existing words from filter list
        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :return:
        """
        error = "Too many arguments, please try again using the following arguments: `k!unfilter [filtered_word]`"
        if too_many_arguments == None:
            await unfilterWord(self, ctx, word)
            await ctx.channel.send("*"+word+"* has been unfiltered.")
            return
        raise Exception(error)

    @commands.command(name="checkFilteredWords", aliases=["check_filtered_words"])
    @commands.check(KoalaBot.is_admin)
    async def checkFilteredWords(self, ctx):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :return:
        """
        all_words_and_types = getListOfWords(self, ctx)
        await ctx.channel.send(embed=buildWordListEmbed(ctx, all_words_and_types[0], all_words_and_types[1], all_words_and_types[2]))

    @commands.command(name="setupModChannel", aliases=["setup_mod_channel"])
    @commands.check(KoalaBot.is_admin)
    async def setupModChannel(self, ctx, channelId, too_many_arguments=None):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :param channelId: The designated channel id for message details
        :return:
        """
        error="Channel not found or too many arguments, please try again: `k!setupModChannel [channelId]`"
        channel = self.bot.get_channel(int(channelId))
        if (channel != None and too_many_arguments == None):
            self.tf_database_manager.new_mod_channel(ctx.guild.id, channelId)
            await ctx.channel.send(embed=buildModerationChannelEmbed(ctx,channel,"Added"))
            return
        raise(Exception(error))
    
    @commands.command(name="removeModChannel", aliases=["remove_mod_channel"])
    @commands.check(KoalaBot.is_admin)
    async def removeModChannel(self, ctx, channelId, too_many_arguments=None):
        """
        Remove a mod channel from the guild
        :param ctx: The discord context
        :param channelId: The designated channel id to be removed
        :return:
        """
        error = "Missing Channel ID or too many arguments remove a mod channel. If you don't know your Channel ID, use `k!listModChannels` to get information on your mod channels."
        channel = self.bot.get_channel(int(channelId))
        if (channel != None and too_many_arguments == None):
            self.tf_database_manager.remove_mod_channel(ctx.guild.id, channelId)
            await ctx.channel.send(embed=buildModerationChannelEmbed(ctx,channel,"Removed"))
            return
        raise Exception(error)

    @commands.command(name="listModChannels", aliases=["list_mod_channels"])
    @commands.check(KoalaBot.is_admin)
    async def listModChannels(self, ctx):
        """
        Get a list of filtered mod channels in the guild
        :param ctx: The discord context
        :return:
        """
        channels = self.tf_database_manager.get_mod_channel(ctx.guild.id)
        await ctx.channel.send(embed=buildChannelListEmbed(self, ctx, channels))

    @commands.command(name="ignoreUser")
    @commands.check(KoalaBot.is_admin)
    async def ignoreUser(self, ctx, user, too_many_arguments=None):
        """
        Add a new ignored user to the database
        :param ctx: The discord context
        :param user: The discord mention of the User
        :return:
        """
        error = "Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID, use `k!listModChannels` to get information on your mod channels."  
        ignore_id = ctx.message.mentions[0].id
        ignore_exists = self.bot.get_user(int(ignore_id))
        if (ignore_exists != None):
            self.tf_database_manager.new_ignore(ctx.guild.id, 'user', ignore_id)
            await ctx.channel.send("New ignore added: " + user)
            return
        raise(Exception(error))

    @commands.command(name="ignoreChannel")
    @commands.check(KoalaBot.is_admin)
    async def ignoreChannel(self, ctx, channel, too_many_arguments=None):
        """
        Add a new ignored channel to the database
        :param ctx: The discord context
        :param channel: The discord mention of the Channel
        :return:
        """
        error = "Missing Ignore ID or too many arguments remove a mod channel. If you don't know your Channel ID, use `k!listModChannels` to get information on your mod channels."  
        ignore_id = ctx.message.channel_mentions[0].id
        ignore_exists = self.bot.get_channel(int(ignore_id))
        if (ignore_exists != None):
            self.tf_database_manager.new_ignore(ctx.guild.id, 'channel', ignore_id)
            await ctx.channel.send("New ignore added: " + channel)
            return
        raise(Exception(error))

    @commands.command(name="removeIgnore", aliases=["remove_ignore", "unignore"])
    @commands.check(KoalaBot.is_admin)
    async def removeIgnore(self, ctx, ignore, too_many_arguments=None):
        """
        Remove a previous ignore from the database
        :param ctx: The discord context
        :param ignore: the ignoreId to be removed
        :return:
        """
        if (len(ctx.message.mentions) > 0):
            ignore_id = ctx.message.mentions[0].id
        elif (len(ctx.message.channel_mentions) > 0):
            ignore_id = ctx.message.channel_mentions[0].id
        else:
            raise Exception("No ignore mention found")
        self.tf_database_manager.remove_ignore(ctx.guild.id, ignore_id)
        await ctx.channel.send("Ignore removed: " + str(ignore))
        return
    
    #todo command for seeing list of ignores
    @commands.command(name="listIgnored", aliases=["list_ignored"])
    @commands.check(KoalaBot.is_admin)
    async def listIgnored(self, ctx):
        """
        Get a list all ignored users/channels
        :param ctx: The discord context
        :return:
        """
        ignored= self.tf_database_manager.get_all_ignored(ctx.guild.id)
        await ctx.channel.send(embed=buildIgnoreListEmbed(self, ctx, ignored))

    @commands.Cog.listener()
    async def on_message(self,message):
        """
        Upon receiving a message, it is checked for filtered text and is deleted.
        :param message: The newly received message
        :return:
        """
        if (str(message.channel.type) == 'private'):
            raise Exception(f"DM Messages are ignored {message}")
        elif (str(message.channel.type) == 'text' and message.channel.guild != None): # and not KoalaBot.is_admin and not KoalaBot.is_owner):
            censor_list = self.tf_database_manager.get_filtered_text_for_guild(message.channel.guild.id)
            for word,filter_type,is_regex in censor_list:
                if ((word in message.content or re.search(word,message.content)) and not isIgnored(self, message)):
                    if (filter_type == "risky"):
                        await message.author.send("Watch your language! Your message: '*"+message.content+"*' in "+message.channel.mention+" contains a 'risky' word. This is a warning.")
                        return
                    elif (filter_type == "banned"):
                        await message.author.send("Watch your language! Your message: '*"+message.content+"*' in "+message.channel.mention+" has been deleted by KoalaBot.")
                        await sendToModerationChannels(self, message)
                        await message.delete()
                        return
        
        raise Exception(f"No Guild found! {message}")

def isIgnored(self, message):
    """
    Checks if the user/channel should be ignored
    :param message: The newly receievd message
    :return boolean if should be ignored or not:
    """
    ignore_list_users = self.tf_database_manager.get_ignore_list_users(message.guild.id)
    ignore_list_channels = self.tf_database_manager.get_ignore_list_channels(message.guild.id)
    return message.channel.id in ignore_list_channels or message.author.id in ignore_list_users

def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param  bot: The client of the KoalaBot
    """
    bot.add_cog(TextFilterCog(bot))

async def filterText(self, ctx, text, filter_type, is_regex):
    """
    Calls to the datbase to filter a word
    :param ctx: the discord context
    :param text: the word to be filtered
    :param filter_type: the filter_type of the word to be added
    """
    self.tf_database_manager.new_filtered_text(ctx.guild.id, text, filter_type, is_regex)

async def unfilterWord(self, ctx, word):
    """
    Calls to the database to unfilter a word
    :param ctx: The discord context
    :param word: The word to be unfiltered
    """
    self.tf_database_manager.unfilter_text(ctx.guild.id, word)

def typeExists(filter_type):
    """
    Validates the inputted filter_type
    :param filter_type: The filter type to be checked
    :return: boolean checking if the filter type can be handled by the system, checks for risky, banned or email
    """
    return filter_type == "risky" or filter_type == "banned"

def isModerationChannelAvailable(self, guild_id,):
    """
    Checks if any mod channels exist to be sent to
    :param guild_id: The guild to retrieve mod channels from
    :return: boolean true if mod channel exists, false otherwise
    """
    channels = self.tf_database_manager.get_mod_channel(guild_id)
    return len(channels) > 0

def getListOfWords(self, ctx):
    """
    Gets a list of filtered words and corresponding types in a guild
    :param ctx: the discord context
    :return [all_words, all_types]: a list containing two lists of filtered words and types
    """
    all_words, all_types, all_regex = "", "", ""
    for word, filter_type, regex in self.tf_database_manager.get_filtered_text_for_guild(ctx.guild.id):
        all_words+=word+"\n"
        all_types+=filter_type+"\n"
        all_regex+=regex+"\n"
    return [all_words, all_types, all_regex]

def buildChannelList(self, channels, embed):
    """
    Builds a list of mod channels and adds them to the embed
    :param channels: list of mod channels 
    :param embed: The pre-existing embed to add the channel list fields to
    :return embed: the updated embed with the list of channels appended to
    """
    for channel in channels:
        details = self.bot.get_channel(int(channel[0]))
        if (details != None):
            embed.add_field(name="Name & Channel ID", value=details.mention + " " + str(details.id), inline=False)
        else:
            embed.add_field(name="Channel ID", value=channel[0], inline=False)
    return embed

def buildIgnoreList(self, ignored, embed):
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
        if (details != None):
            embed.add_field(name="Name & ID", value=details.mention + " " + str(details.id), inline=False)
        else:
            embed.add_field(name="ID", value=ig[3], inline=False)
    return embed

async def sendToModerationChannels(self, message):
    """
    Send details about deleted message to mod channels
    :param message: The message in question which is being deleted
    """
    if (isModerationChannelAvailable(self, message.guild.id)):
        channels = self.tf_database_manager.get_mod_channel(message.guild.id)
        for each_chan in channels:
            channel = self.bot.get_channel(id=int(each_chan[0]))
            await channel.send(embed=buildModerationDeletedEmbed(message))

def buildModerationChannelEmbed(ctx, channel, action):
    """
    Builds a moderation embed which display some information about the mod channel being created/removed
    :param ctx: The discord context
    :param channel: The channel to be created/removed
    :param action: either "Added" or "Removed" to tell the user what happened to the mod channel
    :return embed: The moderation embed to be sent to the user
    """
    embed = createDefaultEmbed(ctx)
    embed.title = "Koala Moderation - Mod Channel " + action
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel ID", value=channel.id)
    return embed

def buildWordListEmbed(ctx, all_words, all_types, all_regex):
    """
    Builds the embed that is sent to list all the filtered words
    :param ctx: The discord context
    :param all_words: List of all the filtered words in the guild
    :param all_types: List of all the corresponding filter types for the words in the guild
    :return embed with information about the deleted message:
    """
    embed = createDefaultEmbed(ctx)
    embed.title = "Koala Moderation - Filtered Words"
    embed.add_field(name="Banned Words", value=all_words)
    embed.add_field(name="Filter Types", value=all_types)
    embed.add_field(name="Is Regex?", value=all_regex)
    return embed

def createDefaultEmbed(ctx):
    """
    Creates a default embed that all embeds share
    :param ctx: The discord context
    :return embed with basic information which should be built upon:
    """
    embed = discord.Embed()
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
    return embed

def buildChannelListEmbed(self, ctx, channels):
    """
    Builds the embed that is sent to list all the mod channels
    :param ctx: The discord context
    :param channels: List of channels in the guild
    :return embed with list of mod channels:
    """
    embed = createDefaultEmbed(ctx)
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
    embed.title = "Koala Moderation - Mod Channels"
    embed = buildChannelList(self, channels, embed)
    return embed

def buildIgnoreListEmbed(self, ctx, channels):
    """
    Builds the embed to list all ignored
    :param ctx: The discord context
    :param ignored: List of ignored users/channels
    :return embed with list of mod channels:
    """
    embed = createDefaultEmbed(ctx)
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
    embed.title = "Koala Moderation - Ignored Users/Channels"
    embed = buildIgnoreList(self, channels, embed)
    return embed

def buildModerationDeletedEmbed(message):
    """
    Builds the embed that is sent after a message is deleted for containing a banned word
    :param message: the message object to be deleted
    :return embed with information about the deleted message:
    """
    embed = createDefaultEmbed(message)
    embed.title = "Koala Moderation - Message Deleted"
    embed.add_field(name="Reason",value="Contained banned word")
    embed.add_field(name="User",value=message.author.mention)
    embed.add_field(name="Channel",value=message.channel.mention)
    embed.add_field(name="Message",value=message.content)
    embed.add_field(name="Timestamp",value=message.created_at)
    return embed

def doesWordExist(self, ft_id):
    """
    Checks if word exists in database given an ID
    :param ft_id: filtered text id of word to be removed
    :return boolean of whether the word exists or not:
    """
    return len(self.database_manager.db_execute_select(f"SELECT * FROM TextFilter WHERE filtered_text_id = ?", args=[ft_id])) > 0

def doesIgnoreExist(self, ignore_id):
    """
    Checks if ignore exists in database given an ID
    :param ignore_id: ignore id of ignore to be removed
    :return boolean of whether the ignore exists or not:
    """
    return len(self.database_manager.db_execute_select(f"SELECT * FROM TextFilterIgnoreList WHERE ignore_id = ?", args=[ignore_id])) > 0

class TextFilterDBManager:
    """
    A class for interacting with the Koala text filter database
    """

    def __init__(self, database_manager: KoalaDBManager, bot_client: discord.client):
        """
        Initialises local variables
        :param database_manager:
        :param bot_client:
        """
        self.database_manager = database_manager
        self.bot = bot_client

    def create_tables(self):
        """
        Creates all the tables associated with TextFilter
        :return:
        """
        sql_create_text_filter_table = """
        CREATE TABLE IF NOT EXISTS TextFilter (
        filtered_text_id text NOT NULL,
        guild_id integer NOT NULL,
        filtered_text text NOT NULL,
        filter_type text NOT NULL,
        is_regex boolean NOT NULL,
        PRIMARY KEY (filtered_text_id)
        );"""

        sql_create_mod_table = """
        CREATE TABLE IF NOT EXISTS TextFilterModeration (
        channel_id text NOT NULL,
        guild_id integer NOT NULL,
        PRIMARY KEY (channel_id)
        );"""

        sql_create_ignore_list_table = """
        CREATE TABLE IF NOT EXISTS TextFilterIgnoreList (
        ignore_id text NOT NULL,
        guild_id integer NOT NULL,
        ignore_type text NOT NULL,
        ignore integer NOT NULL,
        PRIMARY KEY (ignore_id)
        );"""

        self.database_manager.db_execute_commit(sql_create_text_filter_table)
        self.database_manager.db_execute_commit(sql_create_mod_table)
        self.database_manager.db_execute_commit(sql_create_ignore_list_table)

    def new_mod_channel(self, guild_id, channel_id):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param channel_id: The new channel for moderation
        :return:
        """
        self.database_manager.db_execute_commit(
            f"INSERT INTO TextFilterModeration (channel_id, guild_id) VALUES (?,?)", args=[channel_id,guild_id])

    def new_filtered_text(self, guild_id, filtered_text, filter_type, is_regex):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :param filtered_type: The filter type (banned or risky)
        :return:
        """
        ft_id = str(guild_id) + filtered_text
        if not doesWordExist(self, ft_id):
            self.database_manager.db_execute_commit(
                f"INSERT INTO TextFilter (filtered_text_id, guild_id, filtered_text, filter_type, is_regex) VALUES (?,?,?,?,?)", args=[ft_id,guild_id,filtered_text,filter_type,is_regex])
            return 
        raise Exception("Filtered word already exists")
            
    def unfilter_text(self, guild_id, filtered_text):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :return:
        """
        ft_id = str(guild_id) + filtered_text
        if doesWordExist(self, ft_id):
            self.database_manager.db_execute_commit(
                f"DELETE FROM TextFilter WHERE filtered_text_id = ?", args=[ft_id])
            return
        raise Exception("Filtered word does not exist")

    def new_ignore(self, guild_id, ignore_type, ignore):
        """
        Add new ignore to database
        :param guild_id: Guild ID to associate ignore to
        :param ignore_type: The type of ignore to add
        :param ignore: Ignore ID to be added
        """
        ignore_id = str(guild_id) + str(ignore)
        if not doesIgnoreExist(self, ignore_id):
            self.database_manager.db_execute_commit(
                f"INSERT INTO TextFilterIgnoreList (ignore_id, guild_id, ignore_type, ignore) VALUES (?,?,?,?)", args=[ignore_id, guild_id, ignore_type,ignore])
            return
        raise Exception("Ignore already exists")

    def remove_ignore(self, guild_id, ignore):
        """
        Remove ignore from database
        :param guild_id: The guild_id to delete the ignore from
        :param ignore: the ignore id to be deleted
        """
        ignore_id = str(guild_id) + str(ignore)
        if doesIgnoreExist(self, ignore_id):
            self.database_manager.db_execute_commit(
                f"DELETE FROM TextFilterIgnoreList WHERE ignore_id=?", args=[ignore_id])
            return
        raise Exception("Ignore does not exist")

    def get_filtered_text_for_guild(self, guild_id):
        """
        Retrieves all filtered words for a specific guild and formats into a nice list of words
        :param guild_id: Guild ID to retrieve filtered words from:
        :return: list of filtered words
        """
        rows = self.database_manager.db_execute_select(f"SELECT * FROM TextFilter WHERE guild_id = ?", args=[guild_id])
        censor_list = []
        for row in rows:
            censor_list.append((row[2], row[3], str(row[4])))
        return censor_list

    def get_ignore_list_channels(self, guild_id):
        """
        Get lists of ignored channels
        :param guild_id: The guild id to get the list from
        :return: list of ignored channels
        """
        rows = self.database_manager.db_execute_select(f"SELECT * FROM TextFilterIgnoreList WHERE guild_id = ? AND ignore_type = ? ", args=[guild_id, "channel"])
        ilist = []
        for row in rows:
            ilist.append((row[3]))
        return ilist
    
    def get_ignore_list_users(self, guild_id):
        """
        Get lists of ignored users
        :param guild_id: The guild id to get the list from
        :return: list of ignored users
        """
        rows = self.database_manager.db_execute_select(f"SELECT * FROM TextFilterIgnoreList WHERE guild_id = ? AND ignore_type = ? ", args=[guild_id, "user"])
        ilist = []
        for row in rows:
            ilist.append((row[3]))
        return ilist
    
    def get_all_ignored(self,guild_id):
        ignored = []
        users = self.database_manager.db_execute_select(f"SELECT * FROM TextFilterIgnoreList WHERE guild_id = ? AND ignore_type = ? ", args=[guild_id, "user"])
        for row in users:
            ignored.append((row))
        channels = self.database_manager.db_execute_select(f"SELECT * FROM TextFilterIgnoreList WHERE guild_id = ? AND ignore_type = ? ", args=[guild_id, "channel"])
        for row in channels:
            ignored.append((row))
        return ignored

    def get_mod_channel(self, guild_id):
        """
        Gets specific mod channels given a guild id
        :param guild_id: Guild ID to retrieve mod channel from
        :return: list of mod channels
        """
        return self.database_manager.db_execute_select(f"SELECT channel_id FROM TextFilterModeration WHERE guild_id = ?;", args=[guild_id])

    def remove_mod_channel(self, guild_id, channel_id):
        """
        Removes a specific mod channel in a guild
        :param guild_id: Guild ID to remove mod channel from
        :param channel_id: Mod channel to be removed
        :return:
        """
        self.database_manager.db_execute_commit(
            f"DELETE FROM TextFilterModeration WHERE guild_id = ? AND channel_id = (?);", args=[guild_id,channel_id])
    
    def fetch_all(self):
        return self.database_manager.db_execute_select(f"SELECT * FROM TextFilter")