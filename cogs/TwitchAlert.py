#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
TODO: Remove TA from x
    - Custom Alerts
"""
# Futures

# Built-in/Generic Imports
import os
import time
import asyncio
import concurrent.futures

# Libs
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Own modules
import KoalaBot
from KoalaBot import KOALA_GREEN
import utils.KoalaUtils
from utils.KoalaDBManager import KoalaDBManager

# Constants
load_dotenv()
DEFAULT_MESSAGE = "{username} is live, come watch!, {stream_link}"
TWITCH_CLIENT_ID = os.environ['TWITCH_TOKEN']
TWITCH_SECRET = os.environ['TWITCH_SECRET']


# Variables

class TwitchAlert(commands.Cog):
    """
        A discord.py cog for alerting when someone goes live on twitch
    """

    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("TwitchAlert", 0, False, True)
        self.ta_database_manager = TwitchAlertDBManager(KoalaBot.database_manager)
        self.ta_database_manager.create_tables()
        self.loop_thread = None
        self.stop_loop = False

    @commands.command(aliases=["twitch_alert create"])
    @commands.check(KoalaBot.is_admin)
    async def create_twitch_alert(self, ctx, *default_live_message):
        """
        Creates a twitch alert that can store twitch users and channels where
        if the user goes live, a notification will be put in the chosen channel
        :param ctx: The discord context of the command
        :param default_live_message: The default live message of users within this Twitch Alert,
        leave empty for program default
        :return:
        """
        # Assigning default message if provided
        if len(default_live_message) == 0:
            default_message = None
        else:
            default_message = " ".join(default_live_message)

        # Creates a new Twitch Alert with the used guild ID and default message if provided
        new_id = self.ta_database_manager.create_new_ta(ctx.message.guild.id, default_message)

        # Returns an embed with information altered
        new_embed = discord.Embed(title="New Twitch Alert Created!", colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {new_id}")
        await ctx.send(embed=new_embed)

    @commands.command(aliases=["twitch_alert add_channel"])
    @commands.check(KoalaBot.is_admin)
    async def add_twitch_alert_to_channel(self, ctx, twitch_alert_id, channel_id):
        """
        Adds a Twitch Alert to a given channel
        :param ctx: The discord context of the command
        :param twitch_alert_id: The Twitch Alert ID which will be put into a given channel
        :param channel_id: The discord channel ID
        :return:
        """
        self.ta_database_manager.add_ta_to_channel(twitch_alert_id, channel_id)

        # Response Message
        new_embed = discord.Embed(title="Added to Channel",
                                  description="channel ID " + channel_id + " Added to Twitch Alert!",
                                  colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {twitch_alert_id}")
        await ctx.send(embed=new_embed)

    @commands.command()
    @commands.check(KoalaBot.is_admin)
    async def add_user_to_twitch_alert(self, ctx, twitch_alert_id, twitch_username, *custom_live_message):
        """
        Add a Twitch user to a Twitch Alert
        :param ctx: The discord context of the command
        :param twitch_alert_id: The Twitch Alert ID the user will be added to
        :param twitch_username: The Twitch Username of the user being added (lowercase)
        :param custom_live_message: the custom live message for this user's alert
        :return:
        """
        # Setting the custom message as required
        if custom_live_message:
            custom_message = " ".join(custom_live_message)
        else:
            custom_message = None

        self.ta_database_manager.add_user_to_ta(twitch_alert_id, twitch_username, custom_message)

        # Response Message
        new_embed = discord.Embed(title="Added User to Twitch Alert", colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {twitch_alert_id}")
        await ctx.send(embed=new_embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When the bot is started up, the loop begins
        :return:
        """
        self.start_loop()

    def start_loop(self):
        """
        Starts the loop check live event loop
        :return:
        """
        if self.loop_thread is None:
            self.stop_loop = False
            self.loop_thread = asyncio.get_event_loop().create_task(self.loop_check_live())
        else:
            raise Exception("Loop is already running!")
        pass

    def end_loop(self):
        """
        Stop the loop check live event loop
        :return:
        """
        if self.loop_thread is not None:
            self.stop_loop = True
            self.loop_thread.cancel()
            self.loop_thread = None
        else:
            raise Exception("Loop is not running!")
        pass

    async def loop_check_live(self):
        """
        A loop that continually checks the live status of users and
        sends alerts when online, removing them when offline
        :return:
        """
        print("Twitch Alert Loop Started")
        while not self.stop_loop:
            sql_find_users = """SELECT twitch_username FROM UserInTwitchAlert"""
            users = self.ta_database_manager.database_manager.db_execute_select(sql_find_users)
            usernames = []
            users_left = 100
            for user in users:
                usernames.append(user[0])
                users_left -= 1
                if users_left == 0 or users[-1] == user:
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        user_streams = await asyncio.get_event_loop(). \
                            run_in_executor(pool, self.ta_database_manager.twitch_handler.get_streams_data, usernames)
                    users_left = 100

                    # Deals with online streams
                    for user_result in user_streams:
                        if user_result.get('type') == "live":
                            current_username = str.lower(user_result.get("user_name"))
                            print(current_username + " is live")
                            usernames.remove(current_username)

                            sql_find_message_id = f"""
                            SELECT message_id 
                            FROM UserInTwitchAlert 
                            WHERE twitch_username = '{current_username}'"""

                            message_id = self.ta_database_manager.database_manager.db_execute_select(
                                sql_find_message_id)[0]
                            # If no Alert is present
                            if message_id[0] is None:

                                sql_find_channel_id = f"""
                                SELECT TwitchAlertInChannel.twitch_alert_id, channel_id 
                                FROM TwitchAlertInChannel 
                                JOIN TwitchAlerts TA on TwitchAlertInChannel.twitch_alert_id = TA.twitch_alert_id 
                                JOIN UserInTwitchAlert UITA on TA.twitch_alert_id = UITA.twitch_alert_id 
                                WHERE UITA.twitch_username = '{current_username}'"""
                                results = self.ta_database_manager.database_manager.db_execute_select(
                                    sql_find_channel_id)

                                for result in results:
                                    channel = self.bot.get_channel(id=result[1])
                                    with concurrent.futures.ThreadPoolExecutor() as pool2:
                                        user_account = await asyncio.get_event_loop(). \
                                            run_in_executor(pool2,
                                                            self.ta_database_manager.twitch_handler.get_user_data,
                                                            user_result.get("user_name"))

                                        game_details = await asyncio.get_event_loop(). \
                                            run_in_executor(pool2,
                                                            self.ta_database_manager.twitch_handler.get_game_data,
                                                            user_result.get("game_id"))

                                    new_message = await channel.send(
                                        embed=create_live_embed(user_result, user_account, game_details))

                                    sql_update_message_id = f"""
                                    UPDATE UserInTwitchAlert 
                                    SET message_id = {new_message.id} 
                                    WHERE twitch_alert_id = {result[0]} 
                                        AND twitch_username = '{current_username}'"""
                                    self.ta_database_manager.database_manager.db_execute_commit(sql_update_message_id)

                    # Deals with remaining offline streams
                    sql_select_offline_streams_with_message_ids = f"""
                    SELECT TAIC.channel_id, message_id
                    FROM UserInTwitchAlert
                    JOIN TwitchAlerts TA on UserInTwitchAlert.twitch_alert_id = TA.twitch_alert_id
                    JOIN TwitchAlertInChannel TAIC on TA.twitch_alert_id = TAIC.twitch_alert_id
                    WHERE message_id NOT NULL 
                    AND twitch_username in ({','.join(['?'] * len(usernames))})"""

                    results = self.ta_database_manager.database_manager.db_execute_select(
                        sql_select_offline_streams_with_message_ids, usernames)
                    for result in results:
                        await (await self.bot.get_channel(result[0]).fetch_message(result[1])).delete()
                    sql_update_offline_streams = f"""
                    UPDATE UserInTwitchAlert
                    SET message_id = NULL
                    WHERE twitch_username in ({','.join(['?'] * len(usernames))})"""
                    self.ta_database_manager.database_manager.db_execute_commit(sql_update_offline_streams, usernames)
            time.sleep(1)
        pass


def create_live_embed(stream_info, user_info, game_info):
    """
    Creates an embed for the go live announcement
    :param stream_info: The stream data from the Twitch API
    :param user_info: The user data for this streamer from the Twitch API
    :param game_info: The game data for this game from the Twitch API
    :return: The embed created
    """
    embed = discord.Embed(colour=KOALA_GREEN)
    embed.title = "<:twitch:734024383957434489>  " + stream_info.get("user_name") + " is now streaming!"

    embed.description = "https://twitch.tv/" + str.lower(stream_info.get("user_name"))
    embed.add_field(name="Stream Title", value=stream_info.get("title"))

    embed.add_field(name="Playing", value=game_info.get("name"))
    embed.set_thumbnail(url=user_info.get("profile_image_url"))

    return embed


class TwitchAPIHandler:
    """
    A wrapper to interact with the twitch API
    """

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_token = self.get_new_twitch_oauth()
        self.headers = {'Client-ID': self.client_id, 'Authorization': 'Bearer ' + self.oauth_token}

    def get_new_twitch_oauth(self):
        """
        Get a new OAuth2 token from twitch using client_id and client_secret
        :return: The new OAuth2 token
        """
        params = (
            ('client_id', self.client_id),
            ('client_secret', self.client_secret),
            ('grant_type', 'client_credentials'),
        )
        response = requests.post('https://id.twitch.tv/oauth2/token', data=params)
        return response.json().get('access_token')

    def requests_get(self, url, params=None):
        """
        Gets a response from a curl get request to the given url using headers of this object
        :param url: The URL to send the request to
        :param params: The parameters of the request
        :return: The response of the request
        """
        result = requests.get(url, headers=self.headers, params=params)
        return result

    def get_streams_data(self, usernames):
        """
        Gets all stream information from a list of given usernames
        :param usernames: The list of usernames
        :return: The JSON data of the request
        """
        url = 'https://api.twitch.tv/helix/streams?'
        return self.requests_get(url, params={'user_login': usernames}).json().get("data")

    def get_user_data(self, username):
        """
        Gets the user information of a given user
        :param username: The display twitch username of the user
        :return: The JSON information of the user's data
        """
        url = 'https://api.twitch.tv/helix/users?login=' + username
        return self.requests_get(url).json().get("data")[0]

    def get_game_data(self, game_id):
        """
        Gets the game information of a given game
        :param game_id: The twitch game ID of a game
        :return: The JSON information of the game's data
        """
        url = 'https://api.twitch.tv/helix/games?id=' + game_id
        return self.requests_get(url).json().get("data")[0]


class TwitchAlertDBManager:
    """
    A class for interacting with the Koala twitch database
    """

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager = database_manager
        self.twitch_handler = TwitchAPIHandler(TWITCH_CLIENT_ID, TWITCH_SECRET)
        self.loop_thread = None

    def get_parent_database_manager(self):
        return self.database_manager

    def create_tables(self):
        """
        Creates all the tables associated with the twitch alert extension
        :return:
        """

        # TwitchAlerts
        sql_create_twitch_alerts_table = """
        CREATE TABLE IF NOT EXISTS TwitchAlerts (
        twitch_alert_id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        guild_id integer NOT NULL,
        default_message text NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        );"""

        # TwitchAlertInChannel
        sql_create_twitch_alert_in_channel_table = """
        CREATE TABLE IF NOT EXISTS TwitchAlertInChannel (
        twitch_alert_id integer NOT NULL,
        channel_id integer NOT NULL,
        PRIMARY KEY (twitch_alert_id, channel_id),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        # UserInTwitchAlert
        sql_create_user_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchAlert (
        twitch_alert_id integer NOT NULL,
        twitch_username text NOT NULL,
        custom_message text,
        message_id integer,
        PRIMARY KEY (twitch_alert_id, twitch_username),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        # TeamInTwitchAlert
        sql_create_team_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS TeamInTwitchAlert (
        twitch_alert_id integer NOT NULL,
        twitch_team_name text NOT NULL,
        custom_message text,
        PRIMARY KEY (twitch_alert_id, twitch_team_name),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        # UserInTwitchTeam
        sql_create_user_in_twitch_team_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
        twitch_team_name text NOT NULL,
        twitch_username text NOT NULL,
        message_id integer,
        PRIMARY KEY (twitch_team_name, twitch_username),        
        FOREIGN KEY (twitch_team_name) REFERENCES TeamInTwitchAlert (twitch_team_name)
        );"""

        # TwitchDisplayInChannel
        sql_create_twitch_display_in_channel_table = """
        CREATE TABLE IF NOT EXISTS TwitchDisplayInChannel (
        twitch_alert_id integer NOT NULL,
        channel_id integer NOT NULL,
        message_id text NOT NULL,
        PRIMARY KEY (twitch_alert_id, channel_id),        
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        # Create Tables
        self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
        self.database_manager.db_execute_commit(sql_create_twitch_alert_in_channel_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)
        self.database_manager.db_execute_commit(sql_create_twitch_display_in_channel_table)

    def create_new_ta(self, guild_id, default_message):
        """
        Creates a new Twitch Alert and gives the ID associated with it
        :param guild_id: The discord guild ID where the Twitch Alert is located
        :param default_message: The default message of users in the Twitch Alert
        :return: The created Twitch Alert ID
        """
        sql_search = [-1]
        new_id = None

        # Creates a new ID which is not already being used within the database
        while sql_search:
            new_id = utils.KoalaUtils.random_id()
            sql_get_new_ta_id = f"""SELECT twitch_alert_id FROM TwitchAlerts WHERE twitch_alert_id={new_id}"""
            sql_search = self.database_manager.db_execute_select(sql_get_new_ta_id)

        # Sets the default message if not provided
        if default_message is None:
            default_message = DEFAULT_MESSAGE

        # Insert new Twitch Alert to database
        sql_insert_twitch_alert = f"""
        INSERT INTO TwitchAlerts(twitch_alert_id, guild_id, default_message) 
        VALUES({new_id},{guild_id},'{default_message}')
        """
        self.database_manager.db_execute_commit(sql_insert_twitch_alert)

        return new_id

    def add_ta_to_channel(self, twitch_alert_id, channel_id):
        """
        Add Twitch Alert to a given channel
        :param twitch_alert_id: The Twitch Alert ID
        :param channel_id: The discord Channel ID
        :return:
        """
        sql_insert_twitch_alert_channel = f"""
        INSERT INTO TwitchAlertInChannel(twitch_alert_id, channel_id) VALUES({twitch_alert_id},'{channel_id}')
        """
        self.database_manager.db_execute_commit(sql_insert_twitch_alert_channel)

    def add_user_to_ta(self, twitch_alert_id, twitch_username, custom_message):
        """
        Add a twitch user to a given Twitch Alert
        :param twitch_alert_id: The Twitch Alert ID
        :param twitch_username: The Twitch username of the user to be added
        :param custom_message: The custom Message of the user's live notification.
            None = use default Twitch Alert message
        :return:
        """
        if custom_message:
            sql_insert_user_twitch_alert = f"""
            INSERT INTO UserInTwitchAlert(twitch_alert_id, twitch_username, custom_message) 
            VALUES({twitch_alert_id},'{str.lower(twitch_username)}', '{custom_message}')
            """
        else:
            sql_insert_user_twitch_alert = f"""
            INSERT INTO UserInTwitchAlert(twitch_alert_id, twitch_username) 
            VALUES({twitch_alert_id},'{str.lower(twitch_username)}')
            """
        self.database_manager.db_execute_commit(sql_insert_user_twitch_alert)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TwitchAlert(bot))
