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

# Constants

# Variables


def format_db_path(directory: str, filename: str):
    """
    Format the path to be used by the database.

    This will be parsed directly into sqlite3 create connection.

    :param directory: The directory for the database file
    :param filename: The filename of the given database
    """
    if directory:
        directory = directory.replace("\\", "/")
        if directory[-1] != "/":
            directory += "/"

        if os.name == 'nt' and directory[1] != ":":
            if directory[0] == "/":
                directory = directory[1:]
            directory = os.getcwd() + directory
    else:
        directory = ""

    if os.name == 'nt' or not ENCRYPTED_DB:
        return directory + "windows_" + filename
    else:
        return directory + filename


class KoalaDBManager:
    """
    The database manager for KoalaBot
    """

    def __init__(self, db_filename, db_secret_key, db_directory=None):
        self.db_file_path = format_db_path(db_directory, db_filename)
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
        """
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
        CONSTRAINT fk_extensions
            FOREIGN KEY (extension_id) 
            REFERENCES KoalaExtensions (extension_id)
            ON DELETE CASCADE 
        );"""

        sql_create_guild_welcome_messages_table = """
        CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
        guild_id integer NOT NULL PRIMARY KEY,
        welcome_message text
        );"""

        self.db_execute_commit(sql_create_guild_welcome_messages_table)
        self.db_execute_commit(sql_create_koala_extensions_table)
        self.db_execute_commit(sql_create_guild_extensions_table)

    def insert_extension(self, extension_id: str, subscription_required: int, available: bool, enabled: bool):
        """
        Inserts a Koala Extension into the KoalaExtensions table

        :param extension_id: The unique extension ID/ name
        :param subscription_required: The required subscription level to unlock this extension
        :param available: Is available to be enabled by the public
            (false for if a special extension is to be enabled in one server only by the devs)
        :param enabled: Is currently enabled and running
            (false if down for maintenance)
        """

        sql_check_extension_exists = """SELECT * FROM KoalaExtensions WHERE extension_id = ?"""

        if len(self.db_execute_select(sql_check_extension_exists, args=[extension_id])) > 0:
            sql_update_extension = """
            UPDATE KoalaExtensions
            SET subscription_required = ?,
                available = ?,
                enabled = ?
            WHERE extension_id = ?"""
            self.db_execute_commit(sql_update_extension, args=[subscription_required, available, enabled, extension_id])

        else:
            sql_insert_extension = """
            INSERT INTO KoalaExtensions 
            VALUES (?,?,?,?)"""

            self.db_execute_commit(sql_insert_extension, args=[extension_id, subscription_required, available, enabled])

    def extension_enabled(self, guild_id, extension_id: str):
        """
        Check if a given extension is enabled in a specific guild

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID
        """
        sql_select_extension = "SELECT extension_id " \
                               "FROM GuildExtensions " \
                               "WHERE guild_id = ?"
        result = self.db_execute_select(sql_select_extension, args=[guild_id])
        return ("All",) in result or (extension_id,) in result

    def give_guild_extension(self, guild_id, extension_id: str):
        """
        Give a guild the given Koala extension

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID
        """
        sql_check_extension_exists = """SELECT * FROM KoalaExtensions WHERE extension_id = ? and available = 1"""
        if len(self.db_execute_select(sql_check_extension_exists, args=[extension_id])) > 0 or extension_id == "All":
            sql_insert_guild_extension = """
            INSERT INTO GuildExtensions 
            VALUES (?,?)"""
            self.db_execute_commit(sql_insert_guild_extension, args=[extension_id, guild_id])
        else:
            raise NotImplementedError(f"{extension_id} is not a valid extension")

    def remove_guild_extension(self, guild_id, extension_id: str):
        """
        Remove a given Koala extension from a guild

        :param guild_id: Discord guild ID for a given server
        :param extension_id: The Koala extension ID
        """
        sql_remove_extension = "DELETE FROM GuildExtensions " \
                               "WHERE extension_id = ? AND guild_id = ?"
        self.db_execute_commit(sql_remove_extension, args=[extension_id, guild_id], pass_errors=True)

    def get_enabled_guild_extensions(self, guild_id: int):
        """
        Gets a list of extensions IDs that are enabled in a server

        :param guild_id: Discord guild ID for a given server
        """
        sql_select_enabled = "SELECT GuildExtensions.extension_id FROM GuildExtensions, KoalaExtensions " \
                             "WHERE KoalaExtensions.extension_id = GuildExtensions.extension_id " \
                             "  AND guild_id = ? " \
                             "  AND available = 1"
        return self.db_execute_select(sql_select_enabled, args=[guild_id], pass_errors=True)

    def get_all_available_guild_extensions(self, guild_id: int):
        """
        Gets all available guild extensions for a given guild

        todo: restrict with rules of subscriptions & enabled state

        :param guild_id: Discord guild ID for a given server
        """
        sql_select_all = "SELECT DISTINCT KoalaExtensions.extension_id " \
                         "FROM KoalaExtensions WHERE available = 1"
        return self.db_execute_select(sql_select_all, pass_errors=True)

    def fetch_all_tables(self):
        """
        Fetches all table names within the database
        """
        return self.db_execute_select("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")

    def clear_all_tables(self, tables):
        """
        Clears al the data from the given tables

        :param tables: a list of all tables to be cleared
        """
        for table in tables:
            self.db_execute_commit('DELETE FROM ' + table[0] + ';')

    def fetch_guild_welcome_message(self, guild_id):
        """
        Fetches the guild welcome message for a given guild

        :param guild_id: Discord guild ID for a given server
        """
        msg = self.db_execute_select("SELECT * FROM GuildWelcomeMessages WHERE guild_id = ?", args=[guild_id])
        if len(msg) == 0:
            return None
        return msg[0][1]

    def update_guild_welcome_message(self, guild_id, new_message: str):
        """
        Update guild welcome message for a given guild

        :param guild_id: Discord guild ID for a given server
        :param new_message: The new guild welcome message to be set
        """
        self.db_execute_commit(
            "UPDATE GuildWelcomeMessages SET welcome_message = ? WHERE guild_id = ?;", args=[new_message, guild_id])
        return new_message

    def remove_guild_welcome_message(self, guild_id):
        """
        Removes the guild welcome message from a given guild

        :param guild_id: Discord guild ID for a given server
        """
        rows = self.db_execute_select("SELECT * FROM GuildWelcomeMessages WHERE guild_id = ?;", args=[guild_id])
        self.db_execute_commit("DELETE FROM GuildWelcomeMessages WHERE guild_id = ?;", args=[guild_id])
        return len(rows)

    def new_guild_welcome_message(self, guild_id):
        """
        Sets the default guild welcome message to a given guild

        :param guild_id: Discord guild ID for a given server
        """
        from cogs import IntroCog
        self.db_execute_commit(
            "INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES (?, ?);",
            args=[guild_id, IntroCog.DEFAULT_WELCOME_MESSAGE])
        return self.fetch_guild_welcome_message(guild_id)
