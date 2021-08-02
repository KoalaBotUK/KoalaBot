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
from datetime import date

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

def inventory_manager_is_enabled(ctx):
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "InventoryManager")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class InventoryManager(commands.Cog):

    def __init__(self, bot, db_manager=None):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("InventoryManager", 0, True, True)
        self.im_database_manager = InventoryManagerDB(KoalaBot.database_manager)
        self.im_database_manager.create_tables()

    def load_csv_into_db(self):
        pass

    @commands.command(name="checkoutItem", aliases=["checkoutItem"])
    @commands.check(verify_is_enabled)
    async def checkout_item(self, ctx, amount_taken=0, item_name=""):
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        current_date = date.today()
        if amount_taken <= 0:
            await ctx.send(f"Please ensure amount taken is greater than 0, you entered {amount_taken}")
        if item_name == "":
            await ctx.send(f"Please ensure item name is ")
        await self.im_database_manager.checkout_item(user_id, amount_taken, current_date, item_name, guild_id)

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
        try:
            self.database_manager.db_execute_commit(
                "INSERT INTO GuildItems (guild_id, item_name, item_info, item_count) VALUES (?, ?, ?, ?);",
                args=[guild_id, item_name, item_info, item_count]
            )
            return True
        except:
            print("Error: InventoryManager, add_item")
            return False

    def checkout_item(self, user_id, amount_taken, date_taken, item_name, guild_id):
        try:
            amount, item_id = self.database_manager.db_execute_select(
                "SELECT item_count, item_id FROM GuildItems WHERE guild_id = ? AND item_name = ? AND message_id = ?;",
                args=[guild_id, item_name]
            )
            if amount > amount_taken:
                new_amount = amount - amount_taken
                self.database_manager.db_execute_commit(
                    "UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_name = ? AND item_id = ?;",
                    args=[new_amount, guild_id, item_name, item_id]
                )
                self.database_manager.db_execute_commit(
                    "INSERT INTO CheckedOutItems (item_id, discord_id, amount_taken, date_taken) VALUES (?, ?, ?, ?);",
                    args=[item_id, user_id, amount_taken, date_taken]
                )
            return True
        except:
            print("Error: InventoryManager, checkout_item")
            return False

    def remove_item(self, guild_id, item_name):
        try:
            self.database_manager.db_execute_commit(
                "DELETE FROM GuildItems WHERE guild_id = ? AND item_name = ?",
                args=[guild_id, item_name]
            )
            return True
        except:
            print("Error: InventoryManager, remove_item")
            return False

    def list_guild_items(self, guild_id):
        try:
            item_list = self.database_manager.db_execute_select(
                "SELECT item_id, item_name, item_description, item_count FROM GuildItems WHERE guild_id = ?;",
                args=[guild_id]
            )
            return item_list
        except:
            print("Error: InventoryManager, list_guild_items")
            return False

    def list_taken_out_items(self, guild_id):
        pass

    def give_back_item(self, discord_id, item_name, amount_given_back, guild_id):
        try:
            user_item_count, item_id = self.database_manager.db_execute_select(
                "SELECT amount_taken, item_id FROM CheckedOutItems WHERE discord_id = ? AND item_name = ?;",
                args=[discord_id, item_name]
            )
            guild_item_count = self.database_manager.db_execute_select(
                "SELECT item_count FROM GuildItems WHERE item_id = ?;",
                args=[item_id]
            )
            self.database_manager.db_execute_commit(
                "UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_id = ?;",
                args=[(guild_item_count + amount_given_back), guild_id, item_id]
            )
            if amount_given_back < user_item_count:
                self.database_manager.db_execute_commit(
                    "UPDATE CheckedOutItems SET item_count = ? WHERE discord_id = ? AND item_id = ?;",
                    args=[(user_item_count - amount_given_back), discord_id, item_id]
                )
            else:
                self.database_manager.db_execute_commit(
                    "DELETE FROM CheckedOutItems WHERE discord_id = ? AND item_id = ?",
                    args=[discord_id, item_id]
                )
            return True
        except:
            print("Error: InventoryManager, give_back_item")
            return False

    def give_back_all_item(self, discord_id, item_name, guild_id):
        try:
            user_count = self.database_manager.db_execute_select(
                "SELECT item_count FROM CheckedOutItems WHERE item_id = ? AND discord_id = ?",
                args=[item_id, discord_id]
            ) 
            self.database_manager.db_execute_commit(
                "DELETE FROM CheckedOutItems WHERE discord_id = ? AND item_id = ?",
                args=[discord_id, item_id]
            )
            current_count = self.database_manager.db_execute_select(
                "SELECT item_count FROM GuildItems WHERE item_id = ? AND guild_id = ?",
                args=[item_id, guild_id]
            )
            new_count = user_count + current_count
            self.database_manager.db_execute_commit(
                "UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_name = ?",
                args=[new_count, guild_id, item_name]
            )
            return True
        except:
            print("Error: InventoryManager, give_back_all_items")
            return False
            

    def search_name(self, item_name, guild_id):
        try:
            item = self.database_manager.db_execute_select(
                "SELECT (item_name, item_info, item_count) FROM GuildItems WHERE item_name = ? AND guild_id = ?",
                args=[item_name, guild_id]
            )
            return item
        except:
            print("Error: InventoryManager, search_name")
            return False

    def search_description(self):
        pass

    def search_number(self, item_count, guild_id):
        try:
            items = self.database_manager.db_execute_select(
                "SELECT (item_name, item_info, item_count) FROM GuildItems WHERE item_count = ? AND guild_id = ?",
                args=[item_count, guild_id]
            )
            return items
        except:
            print("Error: InventoryManager, search_number")
            return False



def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(InventoryManager(bot))
