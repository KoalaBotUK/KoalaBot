#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import asyncio
import concurrent.futures

# Libs
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Own modules
import KoalaBot
from utils.KoalaColours import *
from utils.KoalaUtils import error_embed, is_channel_in_guild, extract_id
from utils.KoalaDBManager import KoalaDBManager

# Constants
load_dotenv()
DEFAULT_MESSAGE = ""
TWITCH_ICON = "https://cdn3.iconfinder.com/data/icons/social-messaging-ui-color-shapes-2-free" \
              "/128/social-twitch-circle-512.png"
TWITCH_CLIENT_ID = os.environ['TWITCH_TOKEN']
TWITCH_SECRET = os.environ['TWITCH_SECRET']


# Variables

def twitch_is_enabled(ctx):
    """
    A command used to check if the guild has enabled twitch alert
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "TwitchAlert")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class TwitchAlert(commands.Cog):
    """
        A discord.py cog for alerting when someone goes live on twitch
    """
    def __init__(self, bot, database_manager=None):

        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        if not database_manager:
            database_manager = KoalaBot.database_manager
        self.bot = bot
        database_manager.create_base_tables()
        database_manager.insert_extension("TwitchAlert", 0, True, True)
        self.ta_database_manager = TwitchAlertDBManager(database_manager, bot)
        self.ta_database_manager.create_tables()
        self.loop_thread = None
        self.loop_team_thread = None
        self.stop_loop = False

    @commands.command(name="twitchEditMsg", aliases=["edit_default_message"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def edit_default_message(self, ctx, raw_channel_id, *default_live_message):
        """
        Creates a twitch alert that can store twitch users and channels where
        if the user goes live, a notification will be put in the chosen channel
        :param ctx: The discord context of the command
        :param raw_channel_id: The channel ID where the twitch alert is being used
        :param default_live_message: The default live message of users within this Twitch Alert,
        leave empty for program default
        :return:
        """
        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            channel_id = ctx.message.channel.id
            default_live_message = (raw_channel_id, )+default_live_message

        # Assigning default message if provided
        if default_live_message is not None and default_live_message != (None,):
            default_message = " ".join(default_live_message)
            if len(default_message)>1000:
                await ctx.send(embed=error_embed("custom_message is too long, try something with less than 1000 characters"))
                return

        else:
            default_message = None

# Creates a new Twitch Alert with the used guild ID and default message if provided
        default_message = self.ta_database_manager.new_ta(ctx.message.guild.id, channel_id, default_message,
                                                          replace=True)

        # Returns an embed with information altered
        new_embed = discord.Embed(title="Default Message Edited", colour=KOALA_GREEN,
                                  description=f"Guild: {ctx.message.guild.id}\n"
                                              f"Channel: {channel_id}\n"
                                              f"Default Message: {default_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {new_id}")
        await ctx.send(embed=new_embed)

    @commands.command(name="twitchAdd", aliases=['add_user_to_twitch_alert'])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def add_user_to_twitch_alert(self, ctx, raw_channel_id, twitch_username=None, *custom_live_message):
        """
        Add a Twitch user to a Twitch Alert
        :param ctx: The discord context of the command
        :param raw_channel_id: The channel ID where the twitch alert is being used
        :param twitch_username: The Twitch Username of the user being added (lowercase)
        :param custom_live_message: the custom live message for this user's alert
        :return:
        """
        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            custom_live_message = (twitch_username,) + custom_live_message
            twitch_username = raw_channel_id
            channel_id = ctx.message.channel.id
        if twitch_username is None:
            raise commands.MissingRequiredArgument("twitch_username is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        default_message = self.ta_database_manager.new_ta(ctx.message.guild.id, channel_id)

        # Setting the custom message as required
        if custom_live_message is not None and custom_live_message != (None,):
            custom_message = " ".join(custom_live_message)
            default_message = custom_message
            if len(default_message)>1000:
                await ctx.send(embed=error_embed("custom_message is too long, try something with less than 1000 characters"))
                return
        else:
            custom_message = None

        self.ta_database_manager.add_user_to_ta(channel_id, twitch_username, custom_message, ctx.message.guild.id)

        # Response Message
        new_embed = discord.Embed(title="Added User to Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitch_username}\n"
                                              f"Message: {default_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {channel_id}")

        await ctx.send(embed=new_embed)

    @commands.command(name="twitchRemove", aliases=['remove_user_from_twitch_alert'])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def remove_user_from_twitch_alert(self, ctx, raw_channel_id, twitch_username=None):
        """
        Removes a user from a Twitch Alert
        :param ctx: the discord context
        :param raw_channel_id: The discord channel ID of the Twitch Alert
        :param twitch_username: The username of the user to be removed
        :return:
        """

        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            twitch_username = raw_channel_id
            channel_id = ctx.message.channel.id
        if twitch_username is None:
            raise commands.MissingRequiredArgument("twitch_username is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.ta_database_manager.remove_user_from_ta(channel_id, twitch_username)
        # Response Message
        new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitch_username}")

        await ctx.send(embed=new_embed)

    @commands.command(name="twitchAddTeam", aliases=["add_team_to_twitch_alert"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def add_team_to_twitch_alert(self, ctx, raw_channel_id, team_name=None, *custom_live_message):
        """
        Add a Twitch team to a Twitch Alert
        :param ctx: The discord context of the command
        :param raw_channel_id: The channel ID where the twitch alert is being used
        :param team_name: The Twitch team being added (lowercase)
        :param custom_live_message: the custom live message for this team's alert
        :return:
        """

        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            custom_live_message = (team_name,) + custom_live_message
            team_name = raw_channel_id
            channel_id = ctx.message.channel.id
        if team_name is None:
            raise commands.MissingRequiredArgument("team_name is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.ta_database_manager.new_ta(ctx.message.guild.id, channel_id, ctx.message.guild.id)

        # Setting the custom message as required
        if custom_live_message is not None and custom_live_message != (None,):
            default_message = " ".join(custom_live_message)
            if len(default_message)>1000:
                await ctx.send(embed=error_embed("custom_message is too long, try something with less than 1000 characters"))
                return
        else:
            default_message = DEFAULT_MESSAGE

        self.ta_database_manager.add_team_to_ta(channel_id, team_name, default_message, ctx.message.guild.id)

        # Response Message
        new_embed = discord.Embed(title="Added Team to Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"Team: {team_name}\n"
                                              f"Message: {default_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {channel_id}")
        await ctx.send(embed=new_embed)

    @commands.command(name="twitchRemoveTeam", aliases=["remove_team_from_twitch_alert"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def remove_team_from_twitch_alert(self, ctx, raw_channel_id, team_name=None):
        """
        Removes a team from a Twitch Alert
        :param ctx: the discord context
        :param raw_channel_id: The discord channel ID of the Twitch Alert
        :param team_name: The Twitch team being added (lowercase)
        :return:
        """

        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            team_name = raw_channel_id
            channel_id = ctx.message.channel.id
        if team_name is None:
            raise commands.MissingRequiredArgument("team_name is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.ta_database_manager.remove_team_from_ta(channel_id, team_name)
        # Response Message
        new_embed = discord.Embed(title="Removed Team from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"Team: {team_name}")

        await ctx.send(embed=new_embed)

    @commands.command(name="twitchList", aliases=["list_twitch_alert"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def list_twitch_alert(self, ctx, raw_channel_id=None):
        """

        :param ctx:
        :param raw_channel_id:
        :return:
        """
        if raw_channel_id == None:
            channel_id = ctx.message.channel.id
        else:
            channel_id = extract_id(raw_channel_id)

        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return
        embed = discord.Embed()
        embed.title = "Twitch Alerts"
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Channel ID: {channel_id}")

        results = self.ta_database_manager.get_users_in_ta(channel_id)
        if results:
            users = ""
            for result in results:
                users += f"{result[0]}\n"
            embed.add_field(name=":bust_in_silhouette: Users", value=users)
        else:
            embed.add_field(name=":bust_in_silhouette: Users", value="None")

        results = self.ta_database_manager.get_teams_in_ta(channel_id)
        if results:
            teams = ""
            for result in results:
                teams += f"{result[0]}\n"
            embed.add_field(name=":busts_in_silhouette: Teams", value=teams)
        else:
            embed.add_field(name=":busts_in_silhouette: Teams", value="None")

        await ctx.send(embed=embed)

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
            self.loop_team_thread = asyncio.get_event_loop().create_task(self.loop_check_team_live())
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
            self.loop_team_thread.cancel()
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
        print("Twitch Alert Loop Starting")
        while not self.stop_loop:

            sql_find_users = "SELECT twitch_username " \
                             "FROM UserInTwitchAlert " \
                             "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                             "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                             "WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id;"
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

                    # user_streams = self.ta_database_manager.twitch_handler.get_streams_data(usernames)
                    users_left = 100

                    # Deals with online streams
                    for streams_details in user_streams:
                        if streams_details.get('type') == "live":
                            current_username = str.lower(streams_details.get("user_name"))
                            # print(current_username + " is live")
                            usernames.remove(current_username)

                            sql_find_message_id = "SELECT UserInTwitchAlert.channel_id, message_id, custom_message, default_message " \
                                                  "FROM UserInTwitchAlert " \
                                                  "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                                                  "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                                                  "WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id " \
                                                  f"WHERE twitch_username = '{current_username}';"

                            results = self.ta_database_manager.database_manager.db_execute_select(
                                sql_find_message_id)

                            new_message_embed = None

                            for result in results:
                                channel = self.bot.get_channel(id=result[0])

                                # If no Alert is posted
                                if result[1] is None:
                                    if new_message_embed is None:
                                        if result[2] is not None:
                                            message = result[2]
                                        else:
                                            message = result[3]

                                        new_message_embed = self.create_alert_embed(streams_details, message)
                                        # with concurrent.futures.ThreadPoolExecutor() as pool3:
                                        #    new_message = await asyncio.get_event_loop(). \
                                        #        run_in_executor(pool3, self.create_alert_message, int(result[0]),
                                        #                        streams_details, message)
                                    new_message = await channel.send(embed=new_message_embed)
                                    sql_update_message_id = f"""
                                    UPDATE UserInTwitchAlert 
                                    SET message_id = {new_message.id} 
                                    WHERE channel_id = {result[0]} 
                                        AND twitch_username = '{current_username}'"""
                                    self.ta_database_manager.database_manager.db_execute_commit(sql_update_message_id)

                    # Deals with remaining offline streams
                    self.ta_database_manager.delete_all_offline_streams(False, usernames)
            await asyncio.sleep(60)
        pass

    def create_alert_embed(self, stream_data, message):
        """
        Creates and sends an alert message
        :param stream_data: The twitch stream data to have in the message
        :param message: The custom message to be added as a description
        :return: The discord message id of the sent message
        """
        user_details = self.ta_database_manager.twitch_handler.get_user_data(
            stream_data.get("user_name"))
        game_details = self.ta_database_manager.twitch_handler.get_game_data(
            stream_data.get("game_id"))
        return create_live_embed(stream_data, user_details, game_details, message)

    async def loop_check_team_live(self):
        """
        A loop to repeatedly send messages if a member of a team is live, and remove it when they are not
        :return:
        """
        print("Twitch Alert Team Loop Starting")
        while not self.stop_loop:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await asyncio.get_event_loop(). \
                    run_in_executor(pool, self.ta_database_manager.update_all_teams_members)

            sql_select_team_users = "SELECT twitch_username, twitch_team_name " \
                                    "FROM UserInTwitchTeam " \
                                    "JOIN TeamInTwitchAlert TITA ON UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id " \
                                    "JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id " \
                                    "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                                    "WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id "

            users_and_teams = self.ta_database_manager.database_manager.db_execute_select(sql_select_team_users)
            usernames = []
            for user in users_and_teams:
                usernames.append(user[0])
            # (usernames)
            with concurrent.futures.ThreadPoolExecutor() as pool2:
                streams_data = await asyncio.get_event_loop(). \
                    run_in_executor(pool2,
                                    self.ta_database_manager.twitch_handler.get_streams_data,
                                    usernames)
            # print(streams_data)

            # Deals with online streams
            for stream_data in streams_data:
                if stream_data.get('type') == "live":
                    current_username = str.lower(stream_data.get("user_name"))
                    # print(current_username + " is live")
                    usernames.remove(current_username)

                    sql_find_message_id = f"""
                    SELECT TITA.channel_id, message_id, TITA.team_twitch_alert_id, custom_message, default_message 
                    FROM UserInTwitchTeam
                    JOIN TeamInTwitchAlert TITA on UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id
                    JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id
                    JOIN (SELECT extension_id, guild_id 
                          FROM GuildExtensions 
                          WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE ON TA.guild_id = GE.guild_id 
                    WHERE twitch_username = '{current_username}'"""

                    results = self.ta_database_manager.database_manager.db_execute_select(
                        sql_find_message_id)

                    new_message_embed = None

                    for result in results:
                        channel = self.bot.get_channel(id=result[0])

                        # If no Alert is posted
                        if result[1] is None:
                            if new_message_embed is None:
                                if result[3] is not None:
                                    message = result[3]
                                else:
                                    message = result[4]
                                new_message_embed = self.create_alert_embed(stream_data, message)

                                # with concurrent.futures.ThreadPoolExecutor() as pool3:
                                #    new_message = await asyncio.get_event_loop(). \
                                #        run_in_executor(pool3, self.create_alert_message, int(result[0]),
                                #                        stream_data, message)
                            new_message = await channel.send(embed=new_message_embed)
                            sql_update_message_id = f"""
                            UPDATE UserInTwitchTeam 
                            SET message_id = {new_message.id} 
                            WHERE team_twitch_alert_id = {result[2]}
                            AND twitch_username = '{current_username}'"""
                            self.ta_database_manager.database_manager.db_execute_commit(sql_update_message_id)

            # Deals with remaining offline streams
            self.ta_database_manager.delete_all_offline_streams(True, usernames)

        await asyncio.sleep(60)
    pass


def create_live_embed(stream_info, user_info, game_info, message):
    """
    Creates an embed for the go live announcement
    :param stream_info: The stream data from the Twitch API
    :param user_info: The user data for this streamer from the Twitch API
    :param game_info: The game data for this game from the Twitch API
    :param message: The custom message to be added as a description
    :return: The embed created
    """
    embed = discord.Embed(colour=KOALA_GREEN)
    if message is not None and message != "":
        embed.description = message

    embed.set_author(name=stream_info.get("user_name") + " is now streaming!",
                     icon_url=TWITCH_ICON)
    embed.title = "https://twitch.tv/" + str.lower(stream_info.get("user_name"))


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

    def requests_get(self, url, headers=None, params=None):
        """
        Gets a response from a curl get request to the given url using headers of this object
        :param headers: the Headers required for the request, will use self.headers by default
        :param url: The URL to send the request to
        :param params: The parameters of the request
        :return: The response of the request
        """
        if headers is None:
            headers = self.headers

        result = requests.get(url, headers=headers, params=params)
        if result.json().get("error"):
            self.get_new_twitch_oauth()
            result = requests.get(url, headers=headers, params=params)

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

    def get_team_users(self, team_id):
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        url = 'https://api.twitch.tv/kraken/teams/' + team_id
        return self.requests_get(url,
                                 headers={'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
                                 ).json().get("users")


class TwitchAlertDBManager:
    """
    A class for interacting with the Koala twitch database
    """

    def __init__(self, database_manager: KoalaDBManager, bot_client: discord.client):
        """
        Initialises local variables
        :param database_manager:
        :param bot_client:
        """
        self.database_manager = database_manager
        self.twitch_handler = TwitchAPIHandler(TWITCH_CLIENT_ID, TWITCH_SECRET)
        self.bot = bot_client

    def get_parent_database_manager(self):
        """
        A getter for the database manager of this object
        :return:
        """
        return self.database_manager

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
        self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)

    def new_ta(self, guild_id, channel_id, default_message=None, replace=False):
        """
        Creates a new Twitch Alert and gives the ID associated with it
        :param guild_id: The discord guild ID where the Twitch Alert is located
        :param channel_id: The discord channel ID of the twitch Alert
        :param default_message: The default message of users in the Twitch Alert
        :param replace: True if the new ta should replace the current if exists
        :return: The new default_message
        """
        sql_find_ta = f"SELECT default_message FROM TwitchAlerts WHERE channel_id={channel_id}"
        message = self.database_manager.db_execute_select(sql_find_ta)
        if message and not replace:
            return message[0][0]

        # Sets the default message if not provided
        if default_message is None:
            default_message = DEFAULT_MESSAGE

        # Insert new Twitch Alert to database
        if replace:
            sql_insert_twitch_alert = f"""
            REPLACE INTO TwitchAlerts(guild_id, channel_id, default_message) 
            VALUES({guild_id},{channel_id},'{default_message}')
            """
        else:
            sql_insert_twitch_alert = f"""
            INSERT INTO TwitchAlerts(guild_id, channel_id, default_message) 
            VALUES({guild_id},{channel_id},'{default_message}')
            """
        self.database_manager.db_execute_commit(sql_insert_twitch_alert)
        return default_message

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
            sql_insert_user_twitch_alert = f"""
            INSERT INTO UserInTwitchAlert(channel_id, twitch_username, custom_message) 
            VALUES({channel_id},'{str.lower(twitch_username)}', '{custom_message}')
            """
        else:
            sql_insert_user_twitch_alert = f"""
            INSERT INTO UserInTwitchAlert(channel_id, twitch_username) 
            VALUES({channel_id},'{str.lower(twitch_username)}')
            """
        self.database_manager.db_execute_commit(sql_insert_user_twitch_alert)

    def remove_user_from_ta(self, channel_id, twitch_username):
        """
        Removes a user from a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_username: The Twitch username of the user to be added
        :return:
        """
        sql_get_message_id = f"""SELECT message_id 
                                 FROM UserInTwitchAlert 
                                 WHERE twitch_username = '{twitch_username}'
                                    AND channel_id = {channel_id}"""
        message_id = self.database_manager.db_execute_select(sql_get_message_id)[0][0]
        if message_id is not None:
            asyncio.get_event_loop().create_task(self.delete_message(message_id, channel_id))
        sql_remove_entry = f"""DELETE FROM UserInTwitchAlert 
                               WHERE twitch_username = '{twitch_username}' AND channel_id = {channel_id}"""
        self.database_manager.db_execute_commit(sql_remove_entry)

    async def delete_message(self, message_id, channel_id):
        """
        Deletes a given discord message
        :param message_id: discord message ID of the message to delete
        :param channel_id: discord channel ID which has the message
        :return:
        """
        await (await self.bot.get_channel(int(channel_id)).fetch_message(message_id)).delete()

    def get_users_in_ta(self, channel_id):
        """
        Returns all users in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the users
        """
        sql_get_users = "SELECT twitch_username FROM UserInTwitchAlert WHERE channel_id = ?"
        return self.database_manager.db_execute_select(sql_get_users, args=[channel_id])


    def get_teams_in_ta(self, channel_id):
        """
        Returns all teams in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the teams
        """
        sql_get_teams = "SELECT twitch_team_name FROM TeamInTwitchAlert WHERE channel_id = ?"
        return self.database_manager.db_execute_select(sql_get_teams, args=[channel_id])



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
            sql_insert_team_twitch_alert = f"""
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name, custom_message) 
            VALUES({channel_id},'{str.lower(twitch_team)}', '{custom_message}')
            """
        else:
            sql_insert_team_twitch_alert = f"""
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name) 
            VALUES({channel_id},'{str.lower(twitch_team)}')
            """
        self.database_manager.db_execute_commit(sql_insert_team_twitch_alert)

    def remove_team_from_ta(self, channel_id, team_name):
        """
        Removes a team from a given twitch alert
        :param channel_id: The channel ID of the Twitch Alert
        :param team_name: The team name of the team to be removed
        :return:
        """
        sql_get_team_alert_id = f"SELECT team_twitch_alert_id " \
                                f"FROM TeamInTwitchAlert " \
                                f"WHERE twitch_team_name = '{team_name}' " \
                                f" AND channel_id = {channel_id}"
        result = self.database_manager.db_execute_select(sql_get_team_alert_id)
        if not result:
            raise AttributeError("Team name not found")
        team_alert_id = result[0][0]
        sql_get_message_id = f"""SELECT UserInTwitchTeam.message_id
                                 FROM UserInTwitchTeam
                                 WHERE team_twitch_alert_id = {team_alert_id}"""
        message_ids = self.database_manager.db_execute_select(sql_get_message_id)
        if message_ids is not None:
            for message_id in message_ids:
                if message_id[0] is not None:
                    asyncio.get_event_loop().create_task(self.delete_message(message_id[0], channel_id))
        sql_remove_users = f"""DELETE FROM UserInTwitchTeam WHERE team_twitch_alert_id = {team_alert_id}"""
        sql_remove_team = f"""DELETE FROM TeamInTwitchAlert WHERE team_twitch_alert_id = {team_alert_id}"""
        self.database_manager.db_execute_commit(sql_remove_users)
        self.database_manager.db_execute_commit(sql_remove_team)

    def update_team_members(self, twitch_team_id, team_name):
        """
        Users in a team are updated to ensure they are assigned to the correct team
        :param twitch_team_id: the team twitch alert id
        :param team_name: the name of the team
        :return:
        """
        users = self.twitch_handler.get_team_users(team_name)
        for user in users:
            sql_add_user = f"""INSERT INTO UserInTwitchTeam(team_twitch_alert_id, twitch_username) 
                               VALUES({twitch_team_id}, '{user.get("name")}')"""
            self.database_manager.db_execute_commit(sql_add_user)

    def update_all_teams_members(self):
        """
        Updates all teams with the current team members
        :return:
        """
        sql_get_teams = f"""SELECT team_twitch_alert_id, twitch_team_name FROM TeamInTwitchAlert"""
        teams_info = self.database_manager.db_execute_select(sql_get_teams)
        for team_info in teams_info:
            self.update_team_members(team_info[0], team_info[1])

    def delete_all_offline_streams(self, team: bool, usernames):
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

        results = self.database_manager.db_execute_select(
            sql_select_offline_streams_with_message_ids, usernames)

        for result in results:
            asyncio.get_event_loop().create_task(self.delete_message(result[0], result[1]))
        self.database_manager.db_execute_commit(sql_update_offline_streams, usernames)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TwitchAlert(bot))
