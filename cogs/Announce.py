#!/usr/bin/env python

"""
Koala Bot Announce feature
Created by: Bill Cao
"""

# Built-in/Generic Imports
import asyncio

# Libs
import discord
from discord.ext import commands
from utils.KoalaUtils import extract_id
from utils import KoalaColours
import time
# Own modules

import KoalaBot


# global check variables
# datetime object for last use date
# 30 days strictly


def announce_is_enabled(ctx):
    """
    A command used to check if the guild has enabled announce
    e.g. @commands.check(announce_is_enabled)

    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Announce")
    except PermissionError:
        result = True

    return result or (str(ctx.guild) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class Announce(commands.Cog):
    """
        A discord.py cog to allow announcements to certain roles.
    """

    messages = {}
    roles = {}
    announce_database_manager = None

    def __init__(self, bot):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("Announce", 0, True, True)
        self.announce_database_manager = AnnounceDBManager(KoalaBot.database_manager)
        self.announce_database_manager.create_tables()

    def not_exceeded_limit(self, guild_id):
        """
        Check if enough days have passed for the user to use the announce function
        :return:
        """
        if self.announce_database_manager.get_last_use_date(guild_id):
            return int(time.time()) - self.announce_database_manager.get_last_use_date(guild_id) > 2592000 #30*24*60*60
        return True

    def has_active_msg(self, guild_id):
        """
        Check if a particular id has an active announcement pending announcement
        :param guild_id: The id of the guild of the command
        :return: Boolean of whether there is an active announcement or not
        """
        return guild_id in self.messages.keys() and self.messages[guild_id] is not None

    def get_role_names(self, guild_id, roles):
        """
        A function to get the names of all the roles the announcement will be sent to
        :param guild_id: The id of the guild
        :return: All the names of the roles that are tagged
        """
        temp = []
        for role in self.roles[guild_id]:
            temp.append(discord.utils.get(roles, id=role).name)
        return temp

    def get_receivers(self, guild_id, roles):
        """
        A function to get the receivers of a particular announcement
        :param guild_id: The id of the guild
        :return: All the receivers of the announcement
        """
        temp = []
        for role in self.roles[guild_id]:
            temp += discord.utils.get(roles, id=role).members
        return list(set(temp))

    def receiver_msg(self, ctx):
        """
        A function to create a string message about receivers
        :param ctx: The context of the bot
        :return: A string message about receivers
        """
        if not self.roles[ctx.guild.id]:
            return f"You are currently sending to Everyone and there are {str(len(ctx.guild.members))} receivers"
        return f"You are currently sending to {self.get_role_names(ctx.guild.id, ctx.guild.roles)} and there are {str(len(self.get_receivers(ctx.guild.id, ctx.guild.roles)))} receivers "

    def construct_embed(self, guild_id):
        """
        Constructing an embedded message from the information stored in the manager
        :param guild_id: The id of the guild
        :return: An embedded message for the announcement
        """
        message = self.messages[guild_id]
        embed: discord.Embed = discord.Embed(title=message.title,
                                             description=message.description, colour=KoalaColours.KOALA_GREEN)
        embed.set_thumbnail(url=message.thumbnail)
        return embed

    @commands.group(name="announce")
    async def announce(self, ctx):
        """
        Use k!announce create to create an announcement
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot.COMMAND_PREFIX}help announce` for more information")

    @commands.check(announce_is_enabled)
    @announce.command(name="create")
    async def create(self, ctx):
        # if not self.not_exceeded_limit(ctx.guild.id):
        #    ctx.send("You have recently sent an announcement and cannot use this function for now")
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("There is currently an active announcement")
        else:
            await ctx.send("Please enter a message")
            message = await self.bot.wait_for("message", timeout=60)
            if not message:
                await ctx.send("Okay, I'll cancel the command.")
                return
            if len(message.content) > 2000:
                await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
                return
            self.messages[ctx.guild.id] = AnnounceMessage(f"This announcement is from {ctx.guild.name}",
                                                          message.content,
                                                          ctx.guild.icon_url)
            self.roles[ctx.guild.id] = []
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
            await ctx.send(self.receiver_msg(ctx))

    @commands.check(announce_is_enabled)
    @announce.command(name="changeTitle")
    async def change_title(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the new title")
            title = await self.bot.wait_for("message", timeout=60)
            if not title:
                await ctx.send("Okay, I'll cancel the command.")
                return
            self.messages[ctx.guild.id].set_title(title.content)
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="changeContent")
    async def change_content(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the new message")
            message = await self.bot.wait_for("message", timeout=60)
            if not message:
                await ctx.send("Okay, I'll cancel the command.")
                return
            if len(message.content) > 2000:
                await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
                return
            self.messages[ctx.guild.id].set_description(message.content)
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="addRole", aliases=["add"])
    async def add_role(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the roles you want to tag separated by space")
            message = await self.bot.wait_for("message", timeout=60)
            if not message:
                await ctx.send("Okay, I'll cancel the command.")
                return
            for new_role in message.content.split():
                role_id = extract_id(new_role)
                if role_id not in self.roles[ctx.guild.id]:
                    self.roles[ctx.guild.id].append(role_id)
            await ctx.send(self.receiver_msg(ctx))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="removeRole", aliases=["remove"])
    async def remove_role(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the roles you want to remove separated by space")
            message = await self.bot.wait_for("message", timeout=60)
            if not message:
                await ctx.send("Okay, I'll cancel the command.")
                return
            for new_role in message.content.split():
                role_id = extract_id(new_role)
                if role_id in self.roles[ctx.guild.id]:
                    self.roles[ctx.guild.id].remove(role_id)
            await ctx.send(self.receiver_msg(ctx))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="preview")
    async def preview(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
            await ctx.send(self.receiver_msg(ctx))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="send")
    async def send(self, ctx):
        print("Hello")
        if self.has_active_msg(ctx.guild.id):
            embed = self.construct_embed(ctx.guild.id)
            ctx.send(embed=self.construct_embed(ctx.guild.id))
            if self.roles[ctx.guild.id]:
                for receiver in self.get_receivers(ctx.guild.id, ctx.guild.roles):
                    await receiver.send(embed=embed)
            else:
                for receiver in ctx.guild.members:
                    await receiver.send(embed=embed)
            self.messages[ctx.guild.id] = None
            self.roles[ctx.guild.id] = []
            self.announce_database_manager.set_last_use_date(ctx.guild.id, int(time.time()))
            await ctx.send("The announcement was made successfully")
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="cancel")
    async def send(self, ctx):
        if self.has_active_msg(ctx.guild.id):
            self.messages[ctx.guild.id] = None
            self.roles[ctx.guild.id] = []
            await ctx.send("The announcement was cancelled successfully")
        else:
            await ctx.send("There is currently no active announcement")


class AnnounceDBManager:
    """
        A class for interacting with the KoalaBot announcement database
    """

    def __init__(self, database_manager: KoalaBot.database_manager):
        """
            initiate variables
        :param database_manager:
        """
        self.database_manager = database_manager

    def create_tables(self):
        """
            create all the tables related to the announce database
        """
        sql_create_usage_tables = """
        CREATE TABLE IF NOT EXISTS GUILDUSAGE (
        guild_id integer NOT NULL,
        last_message_epoch_time integer NOT NULL,
        PRIMARY KEY (guild_id)
        );
        """

        self.database_manager.db_execute_commit(sql_create_usage_tables)

    def get_last_use_date(self, guild_id: int):
        date: int = self.database_manager.db_execute_select(
            f"""SELECT last_message_epoch_time FROM Usage WHERE guild_id = {guild_id}""")
        if not date:
            return
        else:
            return date

    def set_last_use_date(self, guild_id: int, last_time: int):
        if not (self.database_manager.db_execute_select(f"""SELECT * FROM Usage where guild_id = {guild_id}""")):
            self.database_manager.db_execute_commit(
                f"""UPDATE Usage SET last_message_epoch_time = {last_time} WHERE guild_id = {guild_id}""")
        else:
            self.database_manager.db_execute_commit(f"""INSERT INTO Usage VALUES {guild_id},{last_time}""")


class AnnounceMessage:
    """
    A class consisting the information about a announcement message
    """

    def __init__(self, title, message, thumbnail):
        """
        Initiate the message with default thumbnail, title and description
        :param title: The title of the announcement
        :param message: The message included in the announcement
        :param thumbnail: The logo of the server
        """
        self.title = title
        self.description = message
        self.thumbnail = thumbnail

    def set_title(self, title):
        """
        Changing the title of the announcement
        :param title: A string consisting the title
        :return:
        """
        self.title = title

    def set_description(self, message):
        """
        Changing the message in the announcement
        :param message: A string consisting the message
        :return:
        """
        self.description = message

    def set_thumbnail(self, thumbnail):
        """
        Changing the thumbnail picture of the announcement
        :param thumbnail: A url to the picture
        :return:
        """
        self.thumbnail = thumbnail


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Announce(bot))
    print("Announce is ready.")
