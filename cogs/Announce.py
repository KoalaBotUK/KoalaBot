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
from utils import KoalaColours
from utils.KoalaColours import *
from utils.KoalaUtils import error_embed, is_channel_in_guild, extract_id
from utils.KoalaDBManager import KoalaDBManager


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


def to_list(arr: str):
    return arr[1:-1].split(',')


class Announce(commands.Cog, name="Announce"):
    """
        A discord.py cog to allow announcements to certain roles.
    """

    def __init__(self, bot):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("Announce", 0, True, True)
        self.anc_database_manager = AnnounceDBManager(KoalaBot.database_manager)
        self.anc_database_manager.create_tables()

    def not_exceeded_limit(self):
        return int(datetime.now().strftime('%Y%m%d')) - self.anc_database_manager.get_last_use_date() > 30

    @commands.command(name="announce", aliases=["announcement"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(announce_is_enabled)
    async def make_announcement(self, ctx: commands.Context):
        """
            Create a new announcement in a server targeting specific roles
        :param ctx:
        :return:
        """

        while True:
            await ctx.send("Now please enter the message that you want to send")
            message = await self.wait_for("message")
            if not message:
                await ctx.send(
                    "Okay, didn't receive a message. Cancelling command.")
                return
            else:
                if len(message.content) <= 2000:
                    content = message.content
                else:
                    await ctx.send(
                        "The message is too long, please keep the message within 2000 characters")
                    return
            embed: discord.Embed = discord.Embed(title=f"This announcement is from {ctx.guild.name}",
                                                 description=content, colour=KoalaColours.KOALA_GREEN)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)
            await ctx.send("Are you happy with the message you are sending? Please respond with Y if you are")
            reply = await self.wait_for("message")
            if not reply or reply.content == 'Y':
                break
        while True:
            await ctx.send(
                "Please add the roles that you want to tag separated by comma, remove roles by typing in the form -@role_name,or enter Y when you are done")
            roles = await self.wait_for("message")
            receiver = []
            role_list = []
            if not roles:
                await ctx.send("There doesn't seem to be any input, cancelling the command due to inactivity")
                return
            elif roles.content == 'Y':
                if not receiver:
                    receiver = ctx.guild.members
                    roles.content = "everyone"
                    role_list.append(ctx.guild.id)
                break
            else:
                for role in roles.content.split():
                    if role[0] == '-':
                        try:
                            role_list.remove(extract_id(role[1:]))
                        except TypeError:
                            continue
                    else:
                        role_list.append(extract_id(role))
                for member in ctx.guild.members:
                    for role in member.roles:
                        if role.id in role_list:
                            receiver.append(member)
                            break
            await ctx.send(
                f"You will send to {roles.content} and there are {str(len(receiver))} receivers")

        for user in receiver:
            await user.send(embed=embed)

        self.anc_database_manager.set_last_use_date(guild_id=ctx.guild.id, date=datetime.month)
        self.anc_database_manager.add_announcement(guild_id=ctx.guild.id, role_id=str(role_list), message_id=embed.id)


class AnnounceDBManager:
    """
        A class for interacting with the KoalaBot announcement database
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
        :return:
        """
        sql_create_anc_tables = """
        CREATE TABLE IF NOT EXISTS Announcement (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        message_id integer NOT NULL,
        PRIMARY KEY (message_id)
        );
        """
        sql_create_usage_tables = """
        CREATE TABLE IF NOT EXISTS Usage (
        guild_id integer NOT NULL,
        last_date integer NOT NULL
        PRIMARY KEY (guild_id)
        );
        """

        self.database_manager.db_execute_commit(sql_create_anc_tables)
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

    def add_announcement(self, guild_id: int, role_id: str, message_id: int):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO Announcement VALUES {guild_id},{role_id},{message_id}""")

    def get_announcement(self, message_id: int):
        row: Tuple[int, str, int] = self.database_manager.db_execute_select(
            f"""SELECT * FROM Announcement WHERE message_id = {message_id}""")
        if not row:
            return
        else:
            return row[0], to_list(row[1]), row[2]
