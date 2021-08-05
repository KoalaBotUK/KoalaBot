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


class KoalaDBManager:

    def __init__(self, db_file_path, db_secret_key):
        self.db_file_path = db_file_path
        if os.name == 'nt' or not ENCRYPTED_DB:
            self.db_file_path = "windows_" + self.db_file_path
        self.db_secret_key = db_secret_key

    def create_connection(self):
        """ Create a database connection to the SQLite3 database specified in db_file_path

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

        sql_create_guild_setup_table = """
        CREATE TABLE IF NOT EXISTS GuildSetupStatus(
        guild_id integer NOT NULL PRIMARY KEY, 
        accepted_setup BOOLEAN NOT NULL CHECK (accepted_setup IN (0, 1))
        );
        """

        sql_create_guild_dm_email_list_status_table = """
        CREATE TABLE IF NOT EXISTS GuildDMEmailListStatus(
        guild_id integer NOT NULL PRIMARY KEY,
        dm_email_list_status BOOLEAN NOT NULL CHECK (dm_email_list_status IN (0, 1))
        );
        """

        self.db_execute_commit(sql_create_guild_welcome_messages_table)
        self.db_execute_commit(sql_create_koala_extensions_table)
        self.db_execute_commit(sql_create_guild_extensions_table)
        self.db_execute_commit(sql_create_guild_setup_table)
        self.db_execute_commit(sql_create_guild_dm_email_list_status_table)

    def insert_setup_status(self, guild_id):
        """
        Adds a default setup status of 0 (false) for a guild
        :param guild_id: guild ID
        """
        self.db_execute_commit(
            "INSERT INTO GuildSetupStatus VALUES (?, 0 );",
            args=[guild_id])
        return self.fetch_guild_setup_status(guild_id)

    def fetch_guild_setup_status(self, guild_id):
        """
        Gets the setup status for a guild
        :param guild_id: guild ID
        return: the guild setup status
        """
        return ((self.db_execute_select("""
        SELECT accepted_setup
        FROM GuildSetupStatus
        WHERE guild_id = ?
        """, args=[guild_id], pass_errors=True)[0][0]))

    def update_guild_setup_status(self, guild_id):
        """
        Sets the guild setup status from 0 (false) to 1 (true)
        :param guild_id: guild ID
        """
        sql_update_guild_status ="""
        UPDATE
        GuildSetupStatus    
        SET
        accepted_setup = 1
        WHERE
        guild_id = ?"""
        self.db_execute_commit(sql_update_guild_status, args=[guild_id])

    def remove_guild_status(self, guild_id):
        """
        Removes a guild from the GuildSetupStatus table
        :param guild_id: guild ID
        """
        sql_remove_guild_status = """
        DELETE FROM GuildSetupStatus 
        WHERE guild_id = ?
        """
        self.db_execute_commit(sql_remove_guild_status, args=[guild_id], pass_errors=True)

    def insert_email_list_status(self, guild_id):
        """
        Adds a default email list status of 1 (true) for a guild
        :param guild_id: guild ID
        """
        self.db_execute_commit(
            "INSERT INTO GuildDMEmailListStatus VALUES (?, 1 );",
            args=[guild_id])
        return self.fetch_dm_email_list_status(guild_id)

    def fetch_dm_email_list_status(self, guild_id):
        """
        Gets the email list status for a guild
        :param guild_id: guild ID
        :return: the email list status (boolean)
        """
        return (self.db_execute_select("""
        SELECT dm_email_list_status
        FROM GuildDMEmailListStatus
        WHERE guild_id = ?
        """, args=[guild_id], pass_errors=True)[0][0]) != 0

    def update_dm_email_list_status(self, guild_id, toggle):
        """
        Sets the guild email list status to the value of toggle
        :param guild_id: guild ID
        :param toggle: The value to set the email list status to (0 or 1)
        """
        sql_update_dm_email_list_status ="""
        UPDATE
        GuildDMEmailListStatus    
        SET
        dm_email_list_status = ?
        WHERE
        guild_id = ?"""
        self.db_execute_commit(sql_update_dm_email_list_status, args=[toggle, guild_id])

    def remove_dm_email_list_status(self, guild_id):
        """
        Removes a guild from the GuildDMEmailListStatus table
        :param guild_id: guild ID
        """
        sql_remove_dm_email_list_status = """
        DELETE FROM GuildDMEmailListStatus 
        WHERE guild_id = ?
        """
        self.db_execute_commit(sql_remove_dm_email_list_status, args=[guild_id], pass_errors=True)

    def insert_extension(self, extension_id: str, subscription_required: int, available: bool, enabled: bool):
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

    def extension_enabled(self, guild_id, extension_id):
        sql_select_extension = "SELECT extension_id " \
                               "FROM GuildExtensions " \
                               "WHERE guild_id = ?"
        result = self.db_execute_select(sql_select_extension, args=[guild_id])
        return ("All",) in result or (extension_id,) in result

    def give_guild_extension(self, guild_id, extension_id):
        sql_check_extension_exists = """SELECT * FROM KoalaExtensions WHERE extension_id = ? and available = 1"""
        if len(self.db_execute_select(sql_check_extension_exists, args=[extension_id])) > 0 or extension_id == "All":
            sql_insert_guild_extension = """
            INSERT INTO GuildExtensions 
            VALUES (?,?)"""
            self.db_execute_commit(sql_insert_guild_extension, args=[extension_id, guild_id])
        else:
            raise NotImplementedError(f"{extension_id} is not a valid extension")

    def remove_guild_extension(self, guild_id, extension_id):
        sql_remove_extension = "DELETE FROM GuildExtensions " \
                               "WHERE extension_id = ? AND guild_id = ?"
        self.db_execute_commit(sql_remove_extension, args=[extension_id, guild_id], pass_errors=True)

    def get_enabled_guild_extensions(self, guild_id: int):
        sql_select_enabled = "SELECT GuildExtensions.extension_id FROM GuildExtensions, KoalaExtensions " \
                             "WHERE KoalaExtensions.extension_id = GuildExtensions.extension_id " \
                             "  AND guild_id = ? " \
                             "  AND available = 1"
        return self.db_execute_select(sql_select_enabled, args=[guild_id], pass_errors=True)

    def get_all_available_guild_extensions(self, guild_id: int):
        sql_select_all = "SELECT DISTINCT KoalaExtensions.extension_id " \
                         "FROM KoalaExtensions WHERE available = 1"
        return self.db_execute_select(sql_select_all, pass_errors=True)

    def fetch_all_tables(self):
        return self.db_execute_select("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")

    def clear_all_tables(self, tables):
        for table in tables:
            self.db_execute_commit('DELETE FROM ' + table[0] + ';')

    def fetch_guild_welcome_message(self, guild_id):
        msg = self.db_execute_select("SELECT * FROM GuildWelcomeMessages WHERE guild_id = ?", args=[guild_id])
        if len(msg) == 0:
            return None
        return msg[0][1]

    def update_guild_welcome_message(self, guild_id, new_message: str):
        self.db_execute_commit(
            "UPDATE GuildWelcomeMessages SET welcome_message = ? WHERE guild_id = ?;", args=[new_message, guild_id])
        return new_message

    def remove_guild_welcome_message(self, guild_id):
        rows = self.db_execute_select("SELECT * FROM GuildWelcomeMessages WHERE guild_id = ?;", args=[guild_id])
        self.db_execute_commit("DELETE FROM GuildWelcomeMessages WHERE guild_id = ?;", args=[guild_id])
        return len(rows)

    def new_guild_welcome_message(self, guild_id):
        from cogs import IntroCog
        self.db_execute_commit(
            "INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES (?, ?);",
            args=[guild_id, IntroCog.DEFAULT_WELCOME_MESSAGE])
        return self.fetch_guild_welcome_message(guild_id)
