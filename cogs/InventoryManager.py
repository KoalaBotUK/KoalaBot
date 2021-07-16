#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
import string
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager

# Constants
load_dotenv()
GMAIL_EMAIL = os.environ.get('GMAIL_EMAIL')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')


# Variables


class InventoryManager(commands.Cog):

    def __init__(self, bot, db_manager=None):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("InventoryManager", 0, True, True)
        self.rfr_database_manager = InventoryManagerDB(KoalaBot.database_manager)
        self.rfr_database_manager.create_tables()

    def load_csv_into_db(self):
        pass

    def checkout_item(self):
        pass

    def return_item(self):
        pass

    def search_name(self):
        pass

    def search_description(self):
        pass

    def search_amount(self):
        pass

    def show_checked_out(self):
        pass

    def show_all_items(self):
        pass

    def show_not_checked_out_items(self):
        pass

    def notify_equipment_manager(self):
        pass








class InventoryManagerDB:

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager: KoalaDBManager.KoalaDBManager = database_manager

    def create_tables(self):
        guild_items_table = """
        CREATE TABLE IF NOT EXISTS GuildItems (
        item_id integer NOT NULL AUTO_INCREMENT,
        guild_id integer NOT NULL,
        item_name text NOT NULL,
        item_info text,
        item_count integer NOT NULL,
        PRIMARY KEY (item_id)
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        )
        """

        checked_out_items_table = """
        CREATE TABLE IF NOT EXISTS CheckedOutItems (
        item_id integer NOT NULL,
        discord_id integer NOT NULL,
        amount_taken integer NOT NULL,
        date_taken date NOT NULL,
        PRIMARY KEY (item_id, discord_id)
        FOREIGN KEY(item_id) REFERENCES GuildItems (item_id)
        )
        """

        self.database_manager.db_execute_commit(guild_items_table)
        self.database_manager.db_execute_commit(checked_out_items_table)

    def add_item(self, guild_id: int, item_name: str, item_info: str, item_count: int):
        self.database_manager.db_execute_commit(
            "INSERT INTO GuildItems (guild_id, item_name, item_info, item_count) VALUES (?, ?, ?, ?);",
            args=[guild_id, item_name, item_info, item_count])

    def checkout_item(self, user_id, amount_taken, date_taken, item_name, guild_id):
        amount, item_id = self.database_manager.db_execute_select(
            "SELECT item_count, item_id FROM GuildItems WHERE guild_id = ? AND item_name = ? AND message_id = ?;",
            args=[guild_id, item_name])
        if amount > amount_taken:
            new_amount = amount - amount_taken
            self.database_manager.db_execute_commit(
                "UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_name = ? AND item_id = ?;",
                args=[new_amount, guild_id, item_name, item_id])
            self.database_manager.db_execute_commit(
                "INSERT INTO CheckedOutItems (item_id, discord_id, amount_taken, date_taken) VALUES (?, ?, ?, ?);",
                args=[item_id, user_id, amount_taken, date_taken])

    def remove_item(self, guild_id, item_name):
        self.database_manager.db_execute_commit(
            "DELETE FROM GuildItems WHERE guild_id = ? AND item_name = ?",
            args=[guild_id, item_name])

    def list_guild_items(self, guild_id):
        item_list = self.database_manager.db_execute_select(
            "SELECT item_id, item_name, item_description, item_count FROM GuildItems WHERE guild_id = ?;",
            args=[guild_id])
        if not item_list:
            return
        return item_list

    def list_taken_out_items(self, guild_id):
        pass

    def give_back_item(self, discord_id, item_name, amount_given_back, guild_id):
        user_item_count, item_id = self.database_manager.db_execute_select(
            "SELECT amount_taken, item_id FROM CheckedOutItems WHERE discord_id = ? AND item_name = ?;",
            args=[discord_id, item_name])
        guild_item_count = self.database_manager.db_execute_select(
            "SELECT item_count FROM GuildItems WHERE item_id = ?;",
            args=[item_id])
        self.database_manager.db_execute_commit(
            "UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_id = ?;",
            args=[(guild_item_count + amount_given_back), guild_id, item_id])
        if amount_given_back < user_item_count:
            self.database_manager.db_execute_commit(
                "UPDATE CheckedOutItems SET item_count = ? WHERE discord_id = ? AND item_id = ?;",
                args=[(user_item_count - amount_given_back), discord_id, item_id])
        else:
            self.database_manager.db_execute_commit(
                "DELETE FROM CheckedOutItems WHERE discord_id = ? AND item_id = ?",
                args=[discord_id, item_id])


    def search_name(self):
        pass

    def search_description(self):
        pass

    def search_number(self):
        pass



def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(InventoryManager(bot))
