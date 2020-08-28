#!/usr/bin/env python

"""
Koala Bot SQLite3 Database Manager code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import sqlite3


# Libs


# Own modules


# Constants

# Variables


class KoalaDBManager:

    def __init__(self, db_file_path):
        self.db_file_path = db_file_path

    def create_connection(self):
        """ Create a database connection to the SQLite3 database specified in db_file_path
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
        """ Execute an SQL selection with the connection stored in this object
        :param sql_str: An SQL SELECT statement
        :return: void
        """
        try:
            conn = self.create_connection()
            c = conn.cursor()
            if args:
                c.execute(sql_str, args)
            else:
                c.execute(sql_str)
            results = c.fetchall()
            c.close()
            conn.close()
            return results
        except Exception as e:
            print(e)

    def db_execute_commit(self, sql_str, args=None):
        """ Execute an SQL transaction with the connection stored in this object
        :param sql_str: An SQL transaction
        :param args: Any arguments for the commit
        :return: void
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

        sql_create_guild_welcome_messages_table = """
        CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
        guild_id integer NOT NULL PRIMARY KEY,
        welcome_message text
        );"""

        self.db_execute_commit(sql_create_guild_welcome_messages_table)
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

    def fetch_all_tables(self):
        return self.db_execute_select("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")

    def clear_all_tables(self, tables):
        for table in tables:
            self.db_execute_commit('DELETE FROM ' + table[0] + ';')

    def fetch_guild_welcome_message(self, guild_id):
        msg = self.db_execute_select(f"SELECT * FROM GuildWelcomeMessages WHERE guild_id = {guild_id};")
        if len(msg) == 0:
            return None
        return msg[0][1]

    def update_guild_welcome_message(self, guild_id, new_message: str):
        self.db_execute_commit(
            f"UPDATE GuildWelcomeMessages SET welcome_message = \"{new_message}\" WHERE guild_id = {guild_id};")
        return new_message

    def remove_guild_welcome_message(self, guild_id):
        rows = self.db_execute_select(f"SELECT * FROM GuildWelcomeMessages WHERE guild_id = {guild_id};")
        self.db_execute_commit(f"DELETE FROM GuildWelcomeMessages WHERE guild_id = {guild_id};")
        return len(rows)

    def new_guild_welcome_message(self, guild_id):
        from cogs import IntroCog
        self.db_execute_commit(
            f"INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES ({guild_id}, \"{IntroCog.DEFAULT_WELCOME_MESSAGE}\");")
        return self.fetch_guild_welcome_message(guild_id)
