#!/usr/bin/env python

"""
Koala Bot database management code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import sqlite3


# Libs
import discord
from discord.ext import commands

# Own modules


# Constants

# Variables


class KoalaDBManager:

    def __init__(self, db_file_path):
        self.db_file_path = db_file_path

    def create_connection(self):
        """ create a database connection to the SQLite database
            specified by db_file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file_path)
            return conn
        except Exception as e:
            print(e)

        return conn

    def db_execute_select(self, sql_str, args=None):
        """ execute a sql statement with the connection stored in this object
        :param sql_str: a CREATE TABLE statement
        :return:
        """
        try:
            conn = self.create_connection()
            c = conn.cursor()
            if args:
                c.execute(sql_str,args)
            else:
                c.execute(sql_str)
            results = c.fetchall()
            c.close()
            conn.close()
            return results
        except Exception as e:
            print(e)

    def db_execute_commit(self, sql_str, args=None):
        """ execute a sql statement with the connection stored in this object
        :param sql_str: a CREATE TABLE statement
        :param args: Any arguments for the commit
        :return:
        """
        try:
            conn = self.create_connection()
            c = conn.cursor()
            if args:
                c.execute(sql_str, args)
            else:
                c.execute(sql_str)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            print(e)

    def create_base_tables(self):
        sql_create_koala_extensions_table = """
        CREATE TABLE IF NOT EXISTS KoalaExtensions (
        extension_id text NOT NULL PRIMARY KEY,
        subscription_required integer NOT NULL,
        available boolean NOT NULL,
        enabled boolean NOT NULL
        );"""

        sql_create_guild_extensions_table = """
        CREATE TABLE IF NOT EXISTS GuildExtensions (
        extension_id text NOT NULL,
        guild_id integer NOT NULL,
        PRIMARY KEY (extension_id,guild_id),
        FOREIGN KEY (extension_id) REFERENCES KoalaExtensions (extension_id)
        );"""

        self.db_execute_commit(sql_create_koala_extensions_table)
        self.db_execute_commit(sql_create_guild_extensions_table)

        pass

    def insert_extension(self, extension_id: str, subscription_required: int, available: bool, enabled: bool):
        sql_check_extension_exists = f"""SELECT * FROM KoalaExtensions WHERE extension_id = '{extension_id}'"""

        if len(self.db_execute_select(sql_check_extension_exists)) > 0:
            sql_update_extension = f"""
            UPDATE KoalaExtensions
            SET subscription_required = '{subscription_required}',
                available = '{available}',
                enabled = '{enabled}'
            WHERE extension_id = '{extension_id}'"""
            self.db_execute_commit(sql_update_extension)

        else:
            sql_insert_extension = f"""
            INSERT INTO KoalaExtensions 
            VALUES ('{extension_id}','{subscription_required}','{available}','{enabled}')"""

            self.db_execute_commit(sql_insert_extension)

    def give_guild_extension(self, guild_id, extension_id):
        sql_insert_guild_extension = f"""
        INSERT INTO GuildExtensions 
        VALUES ('{extension_id}','{guild_id}')"""
        self.db_execute_commit(sql_insert_guild_extension)
