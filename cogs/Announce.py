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

import KoalaBot_test
from utils.AnnouncementUtil import AnnounceManager
from utils.KoalaDBManager import KoalaDBManager


def announce_is_enabled(ctx):
    """
    A command used to check if the guild has enabled announce
    e.g. @commands.check(announce_is_enabled)

    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot_test.check_guild_has_ext(ctx, "Announce")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot_test.TEST_USER and KoalaBot_test.is_dpytest)


class Announce(commands.Cog):
    """
        A discord.py cog to allow announcements to certain roles.
    """

    def __init__(self, bot):
        self.bot = bot
        self.announce_manager = AnnounceManager(bot)
        KoalaBot_test.database_manager.create_base_tables()
        KoalaBot_test.database_manager.insert_extension("Announce", 0, True, True)
        self.anc_database_manager = AnnounceDBManager(KoalaBot_test.database_manager)
        self.anc_database_manager.create_tables()

    def not_exceeded_limit(self):
        return int(datetime.now().strftime('%Y%m%d')) - self.anc_database_manager.get_last_use_date() > 30

    @commands.group(name="announce")
    async def announce(self, ctx):
        """
        Use k!announce create to create an announcement
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot_test.COMMAND_PREFIX}help announce` for more information")

    @announce.command(name="create")
    async def create(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await ctx.send("There is currently an active announcement")
        else:
            await self.announce_manager.create_msg(ctx)

    @announce.command(name="createTitle")
    async def change_title(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.change_title(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="changeContent")
    async def change_content(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.change_content(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="addRole")
    async def add_role(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.add_roles(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="removeRole")
    async def remove_role(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.remove_roles(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="preview")
    async def preview(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.preview(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="send")
    async def send(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.send_msg(ctx)
        else:
            await ctx.send("There is currently no active announcement")

    @announce.command(name="cancel")
    async def cancel(self, ctx):
        if self.announce_manager.has_active_msg(ctx.author.id):
            await self.announce_manager.cancel_msg(ctx)
        else:
            await ctx.send("There is currently no active announcement")


class AnnounceDBManager:
    """
        A class for interacting with the KoalaBot_test announcement database
    """

    def __init__(self, database_manager: KoalaDBManager):
        """
            initiate variables
        :param database_manager:
        """
        self.database_manager = database_manager

    def create_tables(self):
        """
            create all the tables related to the announce database
        """
        sql_create_announce_tables = """
        CREATE TABLE IF NOT EXISTS Announcement (
        guild_id integer NOT NULL,
        message_id integer NOT NULL,
        PRIMARY KEY (message_id)
        );
        """
        sql_create_role_tables = """
        CREATE TABLE IF NOT EXISTS ROLES (
        message_id integer NOT NULL,
        role_id integer NOT NULL
        FOREIGN KEY (message_id)
        PRIMARY KEY (role_id)
        );
        """
        sql_create_usage_tables = """
        CREATE TABLE IF NOT EXISTS Usage (
        guild_id integer NOT NULL,
        last_date integer NOT NULL
        PRIMARY KEY (guild_id)
        );
        """

        self.database_manager.db_execute_commit(sql_create_announce_tables)
        self.database_manager.db_execute_commit(sql_create_role_tables)
        self.database_manager.db_execute_commit(sql_create_usage_tables)

    def get_last_use_date(self, guild_id: int):
        date: int = self.database_manager.db_execute_select(
            f"""SELECT last_date FROM Usage WHERE guild_id = {guild_id}""")
        if not date:
            return
        else:
            return date

    def set_last_use_date(self, guild_id: int, date: int):
        if not (self.database_manager.db_execute_select(f"""SELECT * FROM Usage where guild_id = {guild_id}""")):
            self.database_manager.db_execute_commit(
                f"""UPDATE Usage SET last_date = {date} WHERE guild_id = {guild_id}""")
        else:
            self.database_manager.db_execute_commit(f"""INSERT INTO Usage VALUES {guild_id},{date}""")

    def add_announcement(self, guild_id: int, message_id: int):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO Announcement VALUES {guild_id},{message_id}""")

    def add_announcement_role(self, message_id: int, role_id: int):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO ROLES VALUES {message_id},{role_id}"""
        )

    def get_announcement(self, message_id: int):
        row: Tuple[int, str, int] = self.database_manager.db_execute_select(
            f"""SELECT * FROM Announcement WHERE message_id = {message_id}""")
        if not row:
            return
        else:
            return row[0], row[1][1:-1].split(','), row[2]


def setup(bot: KoalaBot_test) -> None:
    """
    Load this cog to the KoalaBot_test.
    :param bot: the bot client for KoalaBot_test
    """
    bot.add_cog(Announce(bot))
    print("Announce is ready.")

