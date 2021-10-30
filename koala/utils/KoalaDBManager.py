#!/usr/bin/env python

"""
Koala Bot SQLite3 Database Manager code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os

# Libs
from dotenv import load_dotenv
load_dotenv()
ENCRYPTED_DB = eval(os.environ.get('ENCRYPTED', "True"))
if ENCRYPTED_DB:
    print(f"ENCRYPTED_DB{ENCRYPTED_DB}")
if os.name == 'nt' or not ENCRYPTED_DB:
    print("Database Encryption Disabled")
    import sqlite3
else:
    print("Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

# Own modules
from koala import db


# Constants

# Variables


class KoalaDBManager:
    """
    The database manager for KoalaBot
    """

    def __init__(self, db_filename, db_secret_key):
        db.setup()
        self.db_file_path = db_filename
        self.db_secret_key = db_secret_key
        self.create_base_tables()

    def create_connection(self):
        """
        Create a database connection to the SQLite3 database specified in db_file_path

        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file_path)
            c = conn.cursor()
            if not (os.name == 'nt' or not ENCRYPTED_DB):
                c.execute('''PRAGMA key="x'{}'"'''.format(self.db_secret_key))

            return conn, c
        except Exception as e:
            print(e)

        return conn

    def db_execute_select(self, sql_str, args=None, pass_errors=False):
        """ Execute an SQL selection with the connection stored in this object

        All Koala Cogs should use this rather than interfacing with sqlite3 directly

        :param sql_str: An SQL SELECT statement
        :param args: Additional args to pass with the sql statement
        :param pass_errors: Raise errors that are raised by this query
        :return:
        """
        try:
            conn, c = self.create_connection()
            if args:
                c.execute(sql_str, args)
            else:
                c.execute(sql_str)
            results = c.fetchall()
            c.close()
            conn.close()
            return results
        except Exception as e:
            if pass_errors:
                raise e
            else:
                print(e)

    def db_execute_commit(self, sql_str, args=None, pass_errors=False):
        """ Execute an SQL transaction with the connection stored in this object

        All Koala Cogs should use this rather than interfacing with sqlite3 directly

        :param sql_str: An SQL transaction
        :param args: Additional args to pass with the sql statement
        :param pass_errors: Raise errors that are raised by this query
        :return: void
        """
        try:
            conn, c = self.create_connection()
            if args:
                c.execute(sql_str, args)
            else:
                c.execute(sql_str)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            if pass_errors:
                raise e
            else:
                print(e)

    def create_base_tables(self):
        """
        Create base tables required for KoalaBot.

        Does not include 'Koala Extension' tables.

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """

        db.setup()

    def insert_extension(self, extension_id: str, subscription_required: int, available: bool, enabled: bool):
        """
        Inserts a Koala Extension into the KoalaExtensions table

        :param extension_id: The unique extension ID/ name
        :param subscription_required: The required subscription level to unlock this extension
        :param available: Is available to be enabled by the public
            (false for if a special extension is to be enabled in one server only by the devs)
        :param enabled: Is currently enabled and running
            (false if down for maintenance)

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        db.insert_extension(extension_id, subscription_required, available, enabled)

    def extension_enabled(self, guild_id, extension_id: str):
        """
        Check if a given extension is enabled in a specific guild

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.extension_enabled(guild_id, extension_id)

    def give_guild_extension(self, guild_id, extension_id: str):
        """
        Give a guild the given Koala extension

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        db.give_guild_extension(guild_id, extension_id)

    def remove_guild_extension(self, guild_id, extension_id: str):
        """
        Remove a given Koala extension from a guild

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        db.remove_guild_extension(guild_id, extension_id)

    def get_enabled_guild_extensions(self, guild_id: int):
        """
        Gets a list of extensions IDs that are enabled in a server

        :param guild_id: Discord guild ID for a given server

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.get_enabled_guild_extensions(guild_id)

    def get_all_available_guild_extensions(self, guild_id: int):
        """
        Gets all available guild extensions for a given guild

        todo: restrict with rules of subscriptions & enabled state

        :param guild_id: Discord guild ID for a given server

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.get_all_available_guild_extensions(guild_id)

    def fetch_all_tables(self):
        """
        Fetches all table names within the database

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.fetch_all_tables()

    def clear_all_tables(self, tables):
        """
        Clears al the data from the given tables

        :param tables: a list of all tables to be cleared

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        db.clear_all_tables(tables)

    def fetch_guild_welcome_message(self, guild_id):
        """
        Fetches the guild welcome message for a given guild

        :param guild_id: Discord guild ID for a given server

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.fetch_guild_welcome_message(guild_id)

    def update_guild_welcome_message(self, guild_id, new_message: str):
        """
        Update guild welcome message for a given guild

        :param guild_id: Discord guild ID for a given server
        :param new_message: The new guild welcome message to be set

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.update_guild_welcome_message(guild_id, new_message)

    def remove_guild_welcome_message(self, guild_id):
        """
        Removes the guild welcome message from a given guild

        :param guild_id: Discord guild ID for a given server

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.remove_guild_welcome_message(guild_id)

    def new_guild_welcome_message(self, guild_id):
        """
        Sets the default guild welcome message to a given guild

        :param guild_id: Discord guild ID for a given server

        .. deprecated:: 0.4.5
           This method is now found in base_db
        """
        return db.new_guild_welcome_message(guild_id)
