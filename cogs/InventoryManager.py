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
import csv

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

    def __init__(self, bot):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("InventoryManager", 0, True, True)
        self.im_database_manager = InventoryManagerDB(KoalaBot.database_manager)
        self.im_database_manager.create_tables()

    @commands.command(name="insertItemCSV")
    async def load_csv_into_db(self, ctx):
        if ctx.message.attachments:
            content = await ctx.message.attachments[0].read()
            content = content.decode('utf-8')
            ''.join(content)
            content = content.split("\r\n")
            for item_unsplit in content:
                if item_unsplit != "":
                    item = item_unsplit.split(",")
                    self.im_database_manager.add_item(ctx.guild.id, item[0].title(), item[2], item[1])
                    await ctx.send(f"Added {item[1]} {item[0]} to the database")

    @commands.command(name="checkoutItem")
    async def checkout_item(self, ctx, amount_taken=0, item_name="", user_id=None):
        if not user_id:
            user_id = ctx.author.id
        guild_id = ctx.guild.id
        current_date = date.today()
        if amount_taken <= 0:
            await ctx.send(f"Please ensure amount taken is greater than 0, you entered {amount_taken}")
        if item_name == "":
            await ctx.send(f"Please ensure item name is entered")
        self.im_database_manager.db_checkout_item(user_id, amount_taken, current_date, item_name, guild_id)
        await ctx.send(f"{user_id} checked out {amount_taken} {item_name} on {current_date}")

    @commands.command(name="returnItem")
    async def return_item(self, ctx, item_name, item_amount, user_id=""):
        if user_id == "":
            user_id = ctx.author.id
        self.im_database_manager.give_back_item(user_id, item_name, item_amount, ctx.guild.id)
        await ctx.send(f"{item_amount} {item_name} returned to inventory by {user_id}")

    @commands.command(name="insertItem")
    async def insert_item(self, ctx, item_name, item_amount, *, item_info=""):
        guild_id = ctx.guild.id
        self.im_database_manager.add_item(guild_id, item_name.title(), item_info, item_amount)
        await ctx.send(f"Added {item_amount} {item_name} to the database")

    @commands.command(name="searchByName")
    async def search_name(self, ctx, item_name):
        result = self.im_database_manager.search_name(item_name.title(), ctx.guild.id)
        for item in result:
            await ctx.send(f"{item[2]} {item[0]} found, info: {item[1]}")

    @commands.command(name="searchByDescription")
    async def search_description(self, ctx, item_info):
        result = self.im_database_manager.search_description(item_info, ctx.guild.id)
        for item in result:
            await ctx.send(f"{item[2]} {item[0]} found, info: {item[1]}")

    @commands.command(name="searchByAmount")
    async def search_amount(self, ctx, item_amount):
        result = self.im_database_manager.search_number(item_amount, ctx.guild.id)
        for item in result:
            await ctx.send(f"{item[2]} {item[0]} found, info: {item[1]}")

    @commands.command(name="showCheckedOutItems")
    async def show_checked_out(self, ctx):
        results = self.im_database_manager.list_taken_out_items(ctx.guild.id)
        for item in results:
            await ctx.send(f"{item[2]} {item[0]} , info: {item[1]}")

    @commands.command(name="showInventory")
    async def show_inventory_items(self, ctx):
        results = self.im_database_manager.list_guild_items(ctx.guild.id)
        for item in results:
            await ctx.send(f"{item[2]} {item[0]} , info: {item[1]}")

    @commands.command(name="toggleNotifyEquipmentManager")
    async def notify_equipment_manager(self, ctx, toggle, equipment_manager_id=""):
        pass

    @commands.command(name="removeItem")
    async def remove_item(self, ctx, item_name, item_amount=0):
        if item_amount == 0:
            self.im_database_manager.remove_item(ctx.guild.id, item_name.title())
            await ctx.send(f"Removed all {item_name} from the inventory")
        else:
            self.im_database_manager.remove_item_amount(ctx.guild.id, item_name.title(), item_amount)
            await ctx.send(f"Removed {item_amount} {item_name} from the inventory")



class InventoryManagerDB:

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager: KoalaDBManager.KoalaDBManager = database_manager

    def create_tables(self):
        guild_items_table = """
        CREATE TABLE IF NOT EXISTS GuildItems (
        item_id text AUTO_INCREMENT,
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
        item_id text NOT NULL,
        discord_id text NOT NULL,
        amount_taken integer NOT NULL,
        date_taken date NOT NULL,
        PRIMARY KEY (item_id, discord_id)
        FOREIGN KEY(item_id) REFERENCES GuildItems (item_id)
        )
        """

        self.database_manager.db_execute_commit(guild_items_table)
        self.database_manager.db_execute_commit(checked_out_items_table)

    def add_item(self, guild_id, item_name, item_info, item_count):
        try:
            if item_name not in self.get_item_names(guild_id):
                self.database_manager.db_execute_commit(
                    "INSERT INTO GuildItems (guild_id, item_name, item_info, item_count) VALUES (?, ?, ?, ?);",
                    args=[guild_id, item_name, item_info, item_count]
                )
            else:
                old_item_count = self.database_manager.db_execute_select(
                    "SELECT item_count FROM GuildItems WHERE guild_id=? AND item_name=?;",
                    args=[guild_id, item_name]
                )
                new_count = int(item_count) + int(old_item_count[0][0])
                self.database_manager.db_execute_commit(
                    "UPDATE GuildItems SET item_count=? WHERE guild_id=? AND item_name=?;",
                    args=[new_count, guild_id, item_name]
                )
        except Exception as e:
            print(e)

    def get_item_names(self, guild_id):
        try:
            guild_item_names = self.database_manager.db_execute_select(
                "SELECT item_name FROM GuildItems WHERE guild_id=?;",
                args=[guild_id]
            )
            return [item for t in guild_item_names for item in t]
        except Exception as e:
            print(e)

    def db_checkout_item(self, user_id, amount_taken, date_taken, item_name, guild_id):
        try:
            amount, item_id = self.database_manager.db_execute_select(
                "SELECT item_count, item_id FROM GuildItems WHERE guild_id = ? AND item_name = ? AND message_id = ?;",
                args=[guild_id, item_name]
            )
            if amount >= amount_taken:
                self.database_manager.db_execute_commit(
                    "INSERT INTO CheckedOutItems (item_id, discord_id, amount_taken, date_taken) VALUES (?, ?, ?, ?);",
                    args=[item_id, user_id, amount_taken, date_taken]
                )
        except Exception as e:
            print(e)

    def remove_item(self, guild_id, item_name):
        try:
            self.database_manager.db_execute_commit(
                "DELETE FROM GuildItems WHERE guild_id = ? AND item_name = ?",
                args=[guild_id, item_name]
            )
        except Exception as e:
            print(e)

    def remove_item_amount(self, guild_id, item_name, item_amount):
        try:
            item_count = self.database_manager.db_execute_select(
                "SELECT item_count FROM GuildItems WHERE guild_id=? AND item_name=?",
                args=[guild_id, item_name]
            )
            print(item_count)
            if item_amount >= item_count[0][0]:
                self.remove_item(guild_id, item_name)
            else:
                new_amount = item_count[0][0] - item_amount
                update_item_count = """UPDATE GuildItems SET item_count = ? WHERE guild_id = ? AND item_name = ?"""
                print("here")
                self.database_manager.db_execute_commit(
                    update_item_count,
                    args=[new_amount, guild_id, item_name]
                )
                self.database_manager.db_execute_select(
                    "SELECT item_count FROM GuildItems WHERE guild_id = ? AND item_name = ?;",
                    args=[guild_id, item_name]
                )
        except Exception as e:
            print(e)

    def list_guild_items(self, guild_id):
        try:
            item_list = self.database_manager.db_execute_select(
                "SELECT item_name, item_info, item_count FROM GuildItems WHERE guild_id = ?;",
                args=[guild_id]
            )
            return item_list
        except Exception as e:
            print(e)

    def list_taken_out_items(self, guild_id):
        try:
            item_list = self.database_manager.db_execute_select(
                "SELECT item_name, item_info, item_count FROM CheckedOutItems WHERE guild_id = ?;",
                args=[guild_id]
            )
            return item_list
        except Exception as e:
            print(e)

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
        except Exception as e:
            print(e)

    def give_back_all_item(self, discord_id, item_name, guild_id):
        try:
            item_id, user_count = self.database_manager.db_execute_select(
                "SELECT item_id, item"
                " FROM CheckedOutItems WHERE discord_id = ? AND item_name = ? AND guild_id = ?",
                args=[discord_id, item_name, guild_id]
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
        except Exception as e:
            print(e)
            

    def search_name(self, item_name, guild_id):
        try:
            item = self.database_manager.db_execute_select(
                "SELECT item_name, item_info, item_count FROM GuildItems WHERE item_name = ? AND guild_id = ?",
                args=[item_name, guild_id]
            )
            return item
        except Exception as e:
            print(e)

    def search_description(self, item_info, guild_id):
        try:
            item = self.database_manager.db_execute_select(
                "SELECT item_name, item_info, item_count FROM GuildItems WHERE item_info = ? AND guild_id = ?",
                args=[item_info, guild_id]
            )
            return item
        except Exception as e:
            print(e)

    def search_number(self, item_count, guild_id):
        try:
            items = self.database_manager.db_execute_select(
                "SELECT item_name, item_info, item_count FROM GuildItems WHERE item_count = ? AND guild_id = ?",
                args=[item_count, guild_id]
            )
            return items
        except Exception as e:
            print(e)



def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(InventoryManager(bot))
    print("InventoryManager is ready.")
