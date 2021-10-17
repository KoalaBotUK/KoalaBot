# Futures

# Built-in/Generic Imports
import re
import logging
# from sqlalchemy import select, update, insert, and_, or_


# Own modules
import KoalaBot
from utils import KoalaDBManager
from.TwitchApiHandler import TwitchAPIHandler
from .models import TwitchAlerts, TeamInTwitchAlert, UserInTwitchTeam, UserInTwitchAlert
from .utils import TWITCH_KEY, TWITCH_SECRET, DEFAULT_MESSAGE, TWITCH_USERNAME_REGEX
from base_models import Base, engine, session

# Libs
import discord

# Constants

# Variables

class TwitchAlertDBManager(KoalaDBManager.KoalaDBManager):
    """
    A class for interacting with the Koala twitch database
    """

    def __init__(self, bot_client: discord.client, database_path=None):
        """
        Initialises local variables
        :param bot_client:
        """
        if not database_path:
            database_path = KoalaBot.DATABASE_PATH

        Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)

        super().__init__(database_path, KoalaBot.DB_KEY)
        self.twitch_handler = TwitchAPIHandler(TWITCH_KEY, TWITCH_SECRET)
        self.bot = bot_client

    def create_tables(self):
        """
        Creates all the tables associated with the twitch alert extension
        :return:
        """
        # TwitchAlerts
        sql_create_twitch_alerts_table = """
        CREATE TABLE IF NOT EXISTS TwitchAlerts (
        guild_id integer NOT NULL,
        channel_id integer NOT NULL,
        default_message text NOT NULL,
        PRIMARY KEY (guild_id, channel_id),
        CONSTRAINT fk_guild
            FOREIGN KEY (guild_id) 
            REFERENCES GuildExtensions (guild_id)
            ON DELETE CASCADE 
        );"""

        # UserInTwitchAlert
        sql_create_user_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchAlert (
        channel_id integer NOT NULL,
        twitch_username text NOT NULL,
        custom_message text,
        message_id integer,
        PRIMARY KEY (channel_id, twitch_username),
        CONSTRAINT fk_channel
            FOREIGN KEY (channel_id) 
            REFERENCES TwitchAlerts (channel_id)
            ON DELETE CASCADE 
        );"""

        # TeamInTwitchAlert
        sql_create_team_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS TeamInTwitchAlert (
        team_twitch_alert_id integer PRIMARY KEY AUTOINCREMENT, 
        channel_id integer NOT NULL,
        twitch_team_name text NOT NULL,
        custom_message text,
        CONSTRAINT fk_channel
            FOREIGN KEY (channel_id) 
            REFERENCES TwitchAlerts (channel_id)
            ON DELETE CASCADE 
        );"""

        # UserInTwitchTeam
        sql_create_user_in_twitch_team_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
        team_twitch_alert_id text NOT NULL,
        twitch_username text NOT NULL,
        message_id integer,
        PRIMARY KEY (team_twitch_alert_id, twitch_username),
        CONSTRAINT fk_twitch_team_alert
            FOREIGN KEY (team_twitch_alert_id) 
            REFERENCES TeamInTwitchAlert (team_twitch_alert_id)
            ON DELETE CASCADE 
        );"""

        # Create Tables
        self.db_execute_commit(sql_create_twitch_alerts_table)
        self.db_execute_commit(sql_create_user_in_twitch_alert_table)
        self.db_execute_commit(sql_create_team_in_twitch_alert_table)
        self.db_execute_commit(sql_create_user_in_twitch_team_table)

    def new_ta(self, guild_id, channel_id, default_message=None, replace=False):
        """
        Creates a new Twitch Alert and gives the ID associated with it
        :param guild_id: The discord guild ID where the Twitch Alert is located
        :param channel_id: The discord channel ID of the twitch Alert
        :param default_message: The default message of users in the Twitch Alert
        :param replace: True if the new ta should replace the current if exists
        :return: The new default_message
        """
        sql_find_ta = "SELECT default_message FROM TwitchAlerts WHERE channel_id=?"
        message = self.db_execute_select(sql_find_ta, args=[channel_id])
        if message and not replace:
            return message[0][0]

        # Sets the default message if not provided
        if default_message is None:
            default_message = DEFAULT_MESSAGE

        # Insert new Twitch Alert to database
        if replace:
            sql_insert_twitch_alert = """
            REPLACE INTO TwitchAlerts(guild_id, channel_id, default_message) 
            VALUES(?,?,?)
            """
        else:
            sql_insert_twitch_alert = """
            INSERT INTO TwitchAlerts(guild_id, channel_id, default_message) 
            VALUES(?,?,?)
            """
        self.db_execute_commit(sql_insert_twitch_alert, args=[guild_id, channel_id, default_message])
        return default_message

    def get_default_message(self, channel_id):
        """
        Get the set default message for the twitch alert
        :param channel_id: The discord channel ID of the twitch Alert
        :return: The current default_message
        """
        sql_find_ta = "SELECT default_message FROM TwitchAlerts WHERE channel_id= ?"
        return self.db_execute_select(sql_find_ta, args=[channel_id])

    def add_user_to_ta(self, channel_id, twitch_username, custom_message, guild_id=None):
        """
        Add a twitch user to a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_username: The Twitch username of the user to be added
        :param custom_message: The custom Message of the user's live notification.
            None = use default Twitch Alert message
        :param guild_id: The guild ID of the channel
        :return:
        :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
        """
        self.new_ta(guild_id, channel_id)

        if custom_message:
            sql_insert_user_twitch_alert = """
            INSERT INTO UserInTwitchAlert(channel_id, twitch_username, custom_message) 
            VALUES(?, ?, ?)
            """
            self.db_execute_commit(
                sql_insert_user_twitch_alert, args=[channel_id, str.lower(twitch_username), custom_message])
        else:
            sql_insert_user_twitch_alert = """
            INSERT INTO UserInTwitchAlert(channel_id, twitch_username) 
            VALUES(?, ?)
            """
            self.db_execute_commit(
                sql_insert_user_twitch_alert, args=[channel_id, str.lower(twitch_username)])

    async def remove_user_from_ta(self, channel_id, twitch_username):
        """
        Removes a user from a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_username: The Twitch username of the user to be added
        :return:
        """
        sql_get_message_id = "SELECT message_id " \
                             "FROM UserInTwitchAlert " \
                             "WHERE twitch_username = ? " \
                             "AND channel_id = ? "
        message_id = self.db_execute_select(sql_get_message_id,
                                            args=[twitch_username, channel_id])[0][0]
        if message_id is not None:
            await self.delete_message(message_id, channel_id)
        sql_remove_entry = """DELETE FROM UserInTwitchAlert 
                               WHERE twitch_username = ? AND channel_id = ?"""
        self.db_execute_commit(sql_remove_entry, args=[twitch_username, channel_id])

    async def delete_message(self, message_id, channel_id):
        """
        Deletes a given discord message
        :param message_id: discord message ID of the message to delete
        :param channel_id: discord channel ID which has the message
        :return:
        """
        try:
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                logging.warning(f"TwitchAlert: Channel ID {channel_id} does not exist, removing from database")
                sql_remove_invalid_channel = "DELETE FROM TwitchAlerts WHERE channel_id = ?"
                self.db_execute_commit(sql_remove_invalid_channel, args=[channel_id])
                return
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound as err:
            logging.warning(f"TwitchAlert: Message ID {message_id} does not exist, skipping \nError: {err}")
        except discord.errors.Forbidden as err:
            logging.warning(f"TwitchAlert: {err}  Channel ID: {channel_id}")
            sql_remove_invalid_channel = "DELETE FROM TwitchAlerts WHERE channel_id = ?"
            self.db_execute_commit(sql_remove_invalid_channel, args=[channel_id])

    def get_users_in_ta(self, channel_id):
        """
        Returns all users in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the users
        """
        sql_get_users = "SELECT twitch_username FROM UserInTwitchAlert WHERE channel_id = ?"
        return self.db_execute_select(sql_get_users, args=[channel_id])

    def get_teams_in_ta(self, channel_id):
        """
        Returns all teams in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the teams
        """
        sql_get_teams = "SELECT twitch_team_name FROM TeamInTwitchAlert WHERE channel_id = ?"
        return self.db_execute_select(sql_get_teams, args=[channel_id])

    def add_team_to_ta(self, channel_id, twitch_team, custom_message, guild_id=None):
        """
        Add a twitch team to a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_team: The Twitch team to be added
        :param custom_message: The custom Message of the team's live notification.
            None = use default Twitch Alert message
        :param guild_id: The guild ID of the channel
        :return:
        :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
        """
        self.new_ta(guild_id, channel_id)

        if custom_message:
            sql_insert_team_twitch_alert = """
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name, custom_message) 
            VALUES(?, ?, ?)
            """
            self.db_execute_commit(
                sql_insert_team_twitch_alert, args=[channel_id, str.lower(twitch_team), custom_message])
        else:
            sql_insert_team_twitch_alert = """
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name) 
            VALUES(?, ?)
            """
            self.db_execute_commit(
                sql_insert_team_twitch_alert, args=[channel_id, str.lower(twitch_team)])

    async def remove_team_from_ta(self, channel_id, team_name):
        """
        Removes a team from a given twitch alert
        :param channel_id: The channel ID of the Twitch Alert
        :param team_name: The team name of the team to be removed
        :return:
        """
        sql_get_team_alert_id = "SELECT team_twitch_alert_id " \
                                "FROM TeamInTwitchAlert " \
                                "WHERE twitch_team_name = ? " \
                                " AND channel_id = ?"
        result = self.db_execute_select(sql_get_team_alert_id, args=[team_name, channel_id])
        if not result:
            raise AttributeError("Team name not found")
        team_alert_id = result[0][0]
        sql_get_message_id = """SELECT UserInTwitchTeam.message_id
                                 FROM UserInTwitchTeam
                                 WHERE team_twitch_alert_id = ?"""
        message_ids = self.db_execute_select(sql_get_message_id, args=[team_alert_id])
        if message_ids is not None:
            for message_id in message_ids:
                if message_id[0] is not None:
                    await self.delete_message(message_id[0], channel_id)
        sql_remove_users = """DELETE FROM UserInTwitchTeam WHERE team_twitch_alert_id = ?"""
        sql_remove_team = """DELETE FROM TeamInTwitchAlert WHERE team_twitch_alert_id = ?"""
        self.db_execute_commit(sql_remove_users, args=[team_alert_id])
        self.db_execute_commit(sql_remove_team, args=[team_alert_id])

    def update_team_members(self, twitch_team_id, team_name):
        """
        Users in a team are updated to ensure they are assigned to the correct team
        :param twitch_team_id: the team twitch alert id
        :param team_name: the name of the team
        :return:
        """
        if re.search(TWITCH_USERNAME_REGEX, team_name):
            users = self.twitch_handler.get_team_users(team_name)
            for user in users:
                sql_add_user = """INSERT OR IGNORE INTO UserInTwitchTeam(team_twitch_alert_id, twitch_username) 
                                   VALUES(?, ?)"""
                try:
                    self.db_execute_commit(sql_add_user, args=[twitch_team_id, user.get("user_login")],
                                           pass_errors=True)
                except KoalaDBManager.sqlite3.IntegrityError as err:
                    logging.error(f"Twitch Alert: 1034: {err}")

    def update_all_teams_members(self):
        """
        Updates all teams with the current team members
        :return:
        """
        sql_get_teams = """SELECT team_twitch_alert_id, twitch_team_name FROM TeamInTwitchAlert"""
        teams_info = self.db_execute_select(sql_get_teams)
        if teams_info is None:
            return
        for team_info in teams_info:
            self.update_team_members(team_info[0], team_info[1])

    async def delete_all_offline_streams(self, team: bool, usernames):
        """
        A method that deletes all currently offline streams
        :param team: True if the users are from teams, false if individuals
        :param usernames: The usernames of the team members
        :return:
        """
        if team:
            sql_select_offline_streams_with_message_ids = f"""
            SELECT channel_id, message_id
            FROM UserInTwitchTeam
            JOIN TeamInTwitchAlert TITA on UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id
            WHERE message_id NOT NULL
            AND twitch_username in ({','.join(['?'] * len(usernames))})"""

            sql_update_offline_streams = f"""
            UPDATE UserInTwitchTeam
            SET message_id = NULL
            WHERE twitch_username in ({','.join(['?'] * len(usernames))})"""

        else:
            sql_select_offline_streams_with_message_ids = f"""
            SELECT channel_id, message_id
            FROM UserInTwitchAlert
            WHERE message_id NOT NULL
            AND twitch_username in ({','.join(['?'] * len(usernames))})"""

            sql_update_offline_streams = f"""
            UPDATE UserInTwitchAlert
            SET message_id = NULL
            WHERE twitch_username in ({','.join(['?'] * len(usernames))})"""

        results = self.db_execute_select(
            sql_select_offline_streams_with_message_ids, usernames)

        if results is None:
            return
        for result in results:
            await self.delete_message(result[1], result[0])
        self.db_execute_commit(sql_update_offline_streams, usernames)

    def translate_names_to_ids(self):
        """
        Translates usernames and team_names to twitch unique IDs
        """
        # todo: Create a backup before

        if len(self.db_execute_select("SELECT name "
                                      "FROM sqlite_master "
                                      "WHERE type='table' AND (name='UserInTwitchAlert' OR name='TeamInTwitchAlert');"
                                      )) == 0:
            return

        table_name = "UserInTwitchAlert"
        fields = self.db_execute_select(f"PRAGMA table_info({table_name});")
        if fields[1][1] == 'twitch_username':
            self.user_names_to_ids()
        elif fields[1][1] != 'twitch_user_id':
            raise NameError(f"Unexpected field {fields[1][1]} in ")

        table_name = "TeamInTwitchAlert"
        fields = self.db_execute_select(f"PRAGMA table_info({table_name});")
        if fields[2][1] == 'twitch_team_name':
            self.team_names_to_ids()
        elif fields[2][1] != 'twitch_team_id':
            raise NameError(f"Unexpected field {fields[1][1]} in ")

        # todo: remove all current messages from UserInTwitchTeam & update from empty

    def user_names_to_ids(self):
        users_in_twitch_alert = self.db_execute_select("SELECT * FROM UserInTwitchAlert;")
        for user in users_in_twitch_alert:
            try:
                self.db_execute_commit("UPDATE UserInTwitchAlert SET twitch_username=? where twitch_username=?",
                                       args=[(self.twitch_handler.get_user_data(usernames=[user[1]]))[0].get("id"),
                                             user[1]])
            except Exception as err:
                logging.error(f"User not found on Twitch {user}, deleted")
        self.db_execute_commit("ALTER TABLE UserInTwitchAlert RENAME COLUMN twitch_username TO twitch_user_id")

    def team_names_to_ids(self):
        team_in_twitch_alert = self.db_execute_select("SELECT * FROM TeamInTwitchAlert;")
        for team in team_in_twitch_alert:
            try:
                self.db_execute_commit("UPDATE TeamInTwitchAlert SET twitch_team_name=? where twitch_team_name=?",
                                       args=[self.twitch_handler.get_team_data(team[2]).get("id"),
                                             team[2]])
            except Exception as err:
                logging.error(f"Team not found on Twitch {team}, deleted")
        self.db_execute_commit("ALTER TABLE TeamInTwitchAlert RENAME COLUMN twitch_team_name TO twitch_team_id")
