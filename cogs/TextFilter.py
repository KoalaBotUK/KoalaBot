#!/usr/bin/env python

"""
Koala Bot Text Filter Code
"""

# Libs
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Own modules
import KoalaBot
from utils import KoalaDBManager

# Constants
load_dotenv()

# Variables
DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)

class TextFilterCog(commands.Cog):
    """
    A discord.py cog with commands pertaining to the a Text Filter for admins to monitor their server
    """

    def __init__(self, bot):
        self.bot = bot
        self.tf_database_manager = TextFilterDBManager(KoalaBot.database_manager, bot)
        self.tf_database_manager.create_tables()

    @commands.command(name="filter", aliases=["filter_Word"])
    @commands.check(KoalaBot.is_owner)
    async def filter_new_word(self, ctx, word):
        """
        Adds new word to the filtered text list
        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :return:
        """
        self.tf_database_manager.new_filtered_text(ctx.guild.id, word)

    @commands.Cog.listener()
    @commands.check(not KoalaBot.is_admin)
    async def on_message(self,message):
        """
        Upon receiving a message, it is checked for filtered text and is deleted.
        :param message: The newly received message
        :return:
        """
        if (message.guild is not None):
            censor_list = self.tf_database_manager.get_filtered_text_for_guild(message.guild.id)
            if (any(map(message.content.__contains__, censor_list))):
                await message.author.send("Watch your language! Your message: '*"+message.content+"*' in #"+message.channel.name+" has been deleted by KoalaBot.")
                await message.delete()

def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param  bot: The client of the KoalaBot
    """
    bot.add_cog(TextFilterCog(bot))

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
        PRIMARY KEY (filtered_text_id)
        );"""

        self.database_manager.db_execute_commit(sql_create_text_filter_table)

    def new_filtered_text(self, guild_id, filtered_text):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from:
        :param filtered_text: The new word to be filtered
        :return:
        """
        ft_id = str(guild_id) + filtered_text
        self.database_manager.db_execute_commit(
            f"INSERT INTO TextFilter (filtered_text_id, guild_id, filtered_text) VALUES (\"{ft_id}\", {guild_id}, \"{filtered_text}\");")

    def get_filtered_text_for_guild(self, guild_id):
        """
        Retrieves all filtered words for a specific guild and formats into a nice list of words
        :param guild_id: Guild ID to retrieve filtered words from:
        :return: list of filtered words
        """
        rows = self.database_manager.db_execute_select(f"SELECT * FROM TextFilter WHERE guild_id = {guild_id};")
        censor_list = []
        for row in rows:
            censor_list.append(row[2])
        return censor_list
