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
        result = False

    return result or (str(ctx.guild) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class Announce(commands.Cog):
    """
        A discord.py cog to allow announcements to certain roles.
    """

    def __init__(self, bot):
        self.bot = bot
        self.messages = {}
        self.roles = {}
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
            return int(time.time()) - self.announce_database_manager.get_last_use_date(
                guild_id) > 2592000  # 30*24*60*60
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
        :param roles: The list of roles in the guild
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
        :param roles: The list of roles in the guild
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
    @announce.command(name="date")
    async def date(self, ctx):
        print(self.announce_database_manager.get_last_use_date(ctx.guild.id))

    @commands.check(announce_is_enabled)
    @announce.command(name="curr")
    async def curr(self, ctx):
        self.announce_database_manager.set_last_use_date(ctx.guild.id, int(time.time()))

    @commands.check(announce_is_enabled)
    @announce.command(name="create")
    async def create(self, ctx):
        """
        This command creates a new message that will be available for sending
        :param ctx: The context of the bot
        :return:
        """
        if not self.not_exceeded_limit(ctx.guild.id):
            await ctx.send("You have recently sent an announcement and cannot use this function for now")
            return
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
            await ctx.send(f"An announcement has been created for guild {ctx.guild.name}")
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
            await ctx.send(self.receiver_msg(ctx))

    @commands.check(announce_is_enabled)
    @announce.command(name="changeTitle")
    async def change_title(self, ctx):
        """
        This commands changes the title of the embedded message
        :param ctx: The context of the bot
        :return:
        """
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
        """
        This commands changes the content of the embedded message
        :param ctx: The context of the bot
        :return:
        """
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
        """
        This command adds a tagged role from the tagged list
        :param ctx: The context of the bot
        :return:
        """
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
        """
        This command removes a tagged role from the tagged list
        :param ctx: The context of the bot
        :return:
        """
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
        """
        This command posts a constructed embedded message to the channel where the command is invoked
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send(embed=self.construct_embed(ctx.guild.id))
            await ctx.send(self.receiver_msg(ctx))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="send")
    async def send(self, ctx):
        """
        This command sends a pending message
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            embed = self.construct_embed(ctx.guild.id)
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
    async def cancel(self, ctx):
        """
        This command cancels a pending message
        :param ctx: The context of the bot
        :return:
        """
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
        CREATE TABLE IF NOT EXISTS GuildUsage (
        guild_id integer NOT NULL,
        last_message_epoch_time integer NOT NULL,
        PRIMARY KEY (guild_id),
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id)
        );
        """
        self.database_manager.db_execute_commit(sql_create_usage_tables)

    def get_last_use_date(self, guild_id: int):
        """
        Gets the last time when this function was used
        :param guild_id: id of the target guild
        :return:
        """
        row = self.database_manager.db_execute_select(
            """SELECT * FROM GuildUsage WHERE guild_id = ?""", args=[guild_id])
        if not row:
            return
        return row[0][1]

    def set_last_use_date(self, guild_id: int, last_time: int):
        """
        Set the last time when this function was used
        :param guild_id: id of the guild
        :param last_time: time when the function was used
        :return:
        """
        if (self.database_manager.db_execute_select("""SELECT last_message_epoch_time FROM GuildUsage where 
        guild_id = ?""", args=[guild_id])):
            self.database_manager.db_execute_commit(
                """UPDATE GuildUsage SET last_message_epoch_time = ? WHERE guild_id = ?""", args=[last_time, guild_id])
        else:
            self.database_manager.db_execute_commit(
                """INSERT INTO GuildUsage (guild_id,last_message_epoch_time) VALUES (?,?)""",
                args=[guild_id, last_time])


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
