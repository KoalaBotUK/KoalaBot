#!/usr/bin/env python

"""
Koala Bot Announce feature
Created by: Bill Cao
"""

# Built-in/Generic Imports
import asyncio

# Libs
from datetime import datetime
from typing import List, Tuple

from discord.ext import commands, tasks
import discord
from time import strftime

# Own modules
import KoalaBot
from utils.KoalaColours import *
from utils.KoalaUtils import error_embed, is_channel_in_guild, extract_id
from utils.KoalaDBManager import KoalaDBManager

# Variable
MESSAGE_PER_MONTH = 1

def not_exceeded_limit():
    month = datetime.datetime.now().strftime("%m")
    usage_data = AnnounceDBManager.get_guild_uses()
    if usage_data[1] != month:
        AnnounceDBManager.update_month()
        return True
    else:
        return usage_data[0]<MESSAGE_PER_MONTH

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

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class Announce(commands.Cog, name="Announce"):
    """
        A discord.py cog to allow announcements to certain roles.
    """

    def __init__(self, bot):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("Announce",0,True,True)
        self.anc_database_manager = AnnounceDBManager(KoalaBot.database_manager)
        self.anc_database_manager.create_tables()

    @commands.command(name="announce", aliases=["announcement"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(announce_is_enabled)
    @commands.check(not_exceeded_limit)
    def make_announcement(self,ctx: commands.Context):
        """
            Create a new announcement in a server targetting specific roles
        :param ctx:
        :return:
        """
        ctx.send("Please enter the title for the message that you want to send")
        message = await self.wait_for_message(self.bot, ctx)
        msg: discord.message = message[0]
        if not message[0]:
            await ctx.send(
                "Okay, didn't receive a title. Cancelling command.")
            return
        else:
            content = msg.content
        ctx.send("Now please enter the message that you want to send")
        message = await self.wait_for_message(self.bot, ctx)
        msg:discord.message = message[0]
        if not message[0]:
            await ctx.send(
                "Okay, didn't receive a message. Cancelling command.")
            return
        else:
            content = msg.content


class AnnounceDBManager:
    """
        A class for interacting with the KoalaBot announcement database
    """

    def __init__(self,database_manager: KoalaDBManager):
        """
            initiate variables
        :param database_manager:
        """
        self.database_manager = database_manager

    def create_tables(self):
        """
            create all the tables related to the announce database
        :return:
        """
        sql_create_anc_tables="""
        CREATE TABLE IF NOT EXISTS Announcement (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        message_id integer NOT NULL,
        PRIMARY KEY (message_id),
        );
        """
        sql_create_limit_tables="""
        CREATE TABLE IF NOT EXISTS Limits (
        guild_id integer NOT NULL,
        uses integer NOT NULL,
        month integer NOT NULL
        PRIMARY KEY (guild_id)
        );
        """

        self.database_manager.db_execute_commit(sql_create_anc_tables)
        self.database_manager.db_execute_commit(sql_create_limit_tables)

    def get_guild_uses(self, guild_id: int):
        rows: List[Tuple[int, int, int]] = self.database_manager.db_execute_select(
            f"""SELECT uses,month FROM GuildRFRMessages WHERE guild_id = {guild_id};""")
        return rows

    def update_month(self,month: int):
        self.database_manager.db_execute_commit(f"""DPDATE Limits SET uses = 0, month = {month}""")
