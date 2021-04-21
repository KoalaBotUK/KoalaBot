#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import asyncio
import time
import re
import aiohttp
import logging

logging.basicConfig(filename='TwitchAlert.log')

# Libs
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Own modules
import KoalaBot
from utils.KoalaColours import *
from utils.KoalaUtils import error_embed, is_channel_in_guild, extract_id
from utils import KoalaDBManager

# Constants
load_dotenv()
DEFAULT_MESSAGE = ""
TWITCH_ICON = "https://cdn3.iconfinder.com/data/icons/social-messaging-ui-color-shapes-2-free" \
              "/128/social-twitch-circle-512.png"
TWITCH_CLIENT_ID = os.environ['TWITCH_TOKEN']
TWITCH_SECRET = os.environ['TWITCH_SECRET']
TWITCH_USERNAME_REGEX = "^[a-z0-9][a-z0-9_]{3,24}$"

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

    return result


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
        self.running = False
        self.stop_loop = False

    @commands.command(name="twitchEditMsg", aliases=["edit_default_message"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def edit_default_message(self, ctx, raw_channel_id, *default_live_message):
        """
        Edit the default message put in a Twitch Alert Notification
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
            default_live_message = (raw_channel_id,) + default_live_message

        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        # Assigning default message if provided
        if default_live_message is not None and default_live_message != (None,):
            default_message = " ".join(default_live_message)
            if len(default_message) > 1000:
                await ctx.send(embed=error_embed(
                    "custom_message is too long, try something with less than 1000 characters"))
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
        await ctx.send(embed=new_embed)

    @commands.command(name="twitchViewMsg", aliases=["view_default_message"])
    @commands.check(KoalaBot.is_admin)
    @commands.check(twitch_is_enabled)
    async def view_default_message(self, ctx, raw_channel_id=None):
        """
        Shows the current default message for Twitch Alerts
        :param ctx: The discord context of the command
        :param raw_channel_id: The channel ID where the twitch alert is being used
        leave empty for program default
        :return:
        """
        if raw_channel_id is None:
            channel_id = ctx.message.channel.id
        else:
            channel_id = extract_id(raw_channel_id)

        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        # Creates a new Twitch Alert with the used guild ID and default message if provided
        default_message = self.ta_database_manager.get_default_message(channel_id)[0][0]

        # Returns an embed with information altered
        new_embed = discord.Embed(title="Default Message", colour=KOALA_GREEN,
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
            raise discord.errors.InvalidArgument("twitch_username is a required argument that is missing.")
        elif not re.search(TWITCH_USERNAME_REGEX, twitch_username):
            raise discord.errors.InvalidArgument(
                "The given twitch_username is not a valid username (please use lowercase)")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        default_message = self.ta_database_manager.new_ta(ctx.message.guild.id, channel_id)

        # Setting the custom message as required
        if custom_live_message is not None and custom_live_message != (None,):
            custom_message = " ".join(custom_live_message)
            default_message = custom_message
            if len(default_message) > 1000:
                await ctx.send(embed=error_embed(
                    "custom_message is too long, try something with less than 1000 characters"))
                return
        else:
            custom_message = None

        self.ta_database_manager.add_user_to_ta(channel_id, twitch_username, custom_message, ctx.message.guild.id)

        # Response Message
        new_embed = discord.Embed(title="Added User to Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitch_username}\n"
                                              f"Message: {default_message}")

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
            raise discord.errors.InvalidArgument("twitch_username is a required argument that is missing.")

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
            raise discord.errors.InvalidArgument("team_name is a required argument that is missing.")
        elif not re.search(TWITCH_USERNAME_REGEX, team_name):
            raise discord.errors.InvalidArgument(
                "The given team_name is not a valid twitch team name (please use lowercase)")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.ta_database_manager.new_ta(ctx.message.guild.id, channel_id)

        # Setting the custom message as required
        if custom_live_message is not None and custom_live_message != (None,):
            default_message = " ".join(custom_live_message)
            if len(default_message) > 1000:
                await ctx.send(embed=error_embed(
                    "custom_message is too long, try something with less than 1000 characters"))
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
            raise discord.errors.InvalidArgument("team_name is a required argument that is missing.")

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
        Shows all current users and teams in a Twitch Alert
        :param ctx:
        :param raw_channel_id:
        :return:
        """
        if raw_channel_id is None:
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
        if not self.running:
            self.start_loops()

    def start_loops(self):
        self.loop_update_teams.start()
        self.loop_check_team_live.start()
        self.loop_check_live.start()
        self.running = True

    def end_loops(self):
        self.loop_update_teams.cancel()
        self.loop_check_team_live.cancel()
        self.loop_check_live.cancel()
        self.running = False

    @tasks.loop(minutes=1)
    async def loop_check_live(self):
        """
        A loop that continually checks the live status of users and
        sends alerts when online, removing them when offline
        :return:
        """
        start = time.time()
        # logging.info("TwitchAlert: User Loop Started")
        sql_find_users = "SELECT twitch_username " \
                         "FROM UserInTwitchAlert " \
                         "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                         "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                         "WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id;"
        users = self.ta_database_manager.database_manager.db_execute_select(sql_find_users)
        usernames = []
        for user in users:
            if not re.search(TWITCH_USERNAME_REGEX, user[0]):
                sql_remove_invalid_user = "DELETE FROM UserInTwitchAlert WHERE twitch_username = ?"
                self.ta_database_manager.database_manager.db_execute_commit(sql_remove_invalid_user, args=[user[0]])
            else:
                usernames.append(user[0])

        # user_streams = self.ta_database_manager.twitch_handler.get_streams_data(usernames)
        if not usernames:
            return

        user_streams = await self.ta_database_manager.twitch_handler.get_streams_data(usernames)
        if user_streams is None:
            return

        # Deals with online streams
        for streams_details in user_streams:
            try:
                if streams_details.get('type') == "live":
                    current_username = str.lower(streams_details.get("user_name"))
                    usernames.remove(current_username)

                    sql_find_message_id = \
                        "SELECT UserInTwitchAlert.channel_id, message_id, custom_message, default_message " \
                        "FROM UserInTwitchAlert " \
                        "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                        "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                        "WHERE extension_id = 'TwitchAlert' " \
                        "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id " \
                        "WHERE twitch_username = ?;"

                    results = self.ta_database_manager.database_manager.db_execute_select(
                        sql_find_message_id, args=[current_username])

                    new_message_embed = None

                    for result in results:
                        channel_id = result[0]
                        message_id = result[1]
                        custom_message = result[2]
                        channel_default_message = result[3]

                        channel = self.bot.get_channel(id=channel_id)
                        try:
                            # If no Alert is posted
                            if message_id is None:
                                if new_message_embed is None:
                                    if custom_message is not None:
                                        message = custom_message
                                    else:
                                        message = channel_default_message

                                    new_message_embed = await self.create_alert_embed(streams_details, message)

                                if new_message_embed is not None and channel is not None:
                                    new_message = await channel.send(embed=new_message_embed)
                                    sql_update_message_id = """
                                    UPDATE UserInTwitchAlert 
                                    SET message_id = ? 
                                    WHERE channel_id = ? 
                                        AND twitch_username = ?"""
                                    self.ta_database_manager.database_manager.db_execute_commit(
                                        sql_update_message_id, args=[new_message.id, result[0], current_username])
                        except discord.errors.Forbidden as err:
                            logging.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                            sql_remove_invalid_channel = "DELETE FROM TwitchAlerts WHERE channel_id = ?"
                            self.ta_database_manager.database_manager.db_execute_commit(sql_remove_invalid_channel,
                                                                                        args=[channel.id])
            except Exception as err:
                logging.error(f"TwitchAlert: User Loop error {err}")

        # Deals with remaining offline streams
        self.ta_database_manager.delete_all_offline_streams(False, usernames)
        time_diff = time.time() - start
        if time_diff > 5:
            logging.warning(f"TwitchAlert: User Loop Finished in > 5s | {time_diff}s")

    async def create_alert_embed(self, stream_data, message):
        """
        Creates and sends an alert message
        :param stream_data: The twitch stream data to have in the message
        :param message: The custom message to be added as a description
        :return: The discord message id of the sent message
        """
        user_details = await self.ta_database_manager.twitch_handler.get_user_data(
            stream_data.get("user_name"))
        game_details = await self.ta_database_manager.twitch_handler.get_game_data(
            stream_data.get("game_id"))
        return create_live_embed(stream_data, user_details, game_details, message)

    @tasks.loop(minutes=5)
    async def loop_update_teams(self):
        start = time.time()
        # logging.info("TwitchAlert: Started Update Teams")
        await self.ta_database_manager.update_all_teams_members()
        time_diff = time.time() - start
        if time_diff > 5:
            logging.warning(f"TwitchAlert: Teams updated in > 5s | {time_diff}s")

    @tasks.loop(minutes=1)
    async def loop_check_team_live(self):
        """
        A loop to repeatedly send messages if a member of a team is live, and remove it when they are not

        :return:
        """
        start = time.time()
        # logging.info("TwitchAlert: Team Loop Started")
        sql_select_team_users = "SELECT twitch_username, twitch_team_name " \
                                "FROM UserInTwitchTeam " \
                                "JOIN TeamInTwitchAlert TITA " \
                                "  ON UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id " \
                                "JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id " \
                                "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                                "WHERE extension_id = 'TwitchAlert' " \
                                "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id "

        users_and_teams = self.ta_database_manager.database_manager.db_execute_select(sql_select_team_users)
        usernames = []
        for user in users_and_teams:
            if not re.search(TWITCH_USERNAME_REGEX, user[1]):
                sql_remove_invalid_user = "DELETE FROM TeamInTwitchAlert WHERE twitch_team_name = ?"
                self.ta_database_manager.database_manager.db_execute_commit(sql_remove_invalid_user, args=[user[1]])
            else:
                usernames.append(user[0])

        if not usernames:
            return

        streams_data = await self.ta_database_manager.twitch_handler.get_streams_data(usernames)

        if streams_data is None:
            return
        # Deals with online streams
        for stream_data in streams_data:
            try:
                if stream_data.get('type') == "live":
                    current_username = str.lower(stream_data.get("user_name"))
                    usernames.remove(current_username)

                    sql_find_message_id = """
                    SELECT TITA.channel_id, UserInTwitchTeam.message_id, TITA.team_twitch_alert_id, custom_message, 
                      default_message 
                    FROM UserInTwitchTeam
                    JOIN TeamInTwitchAlert TITA on UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id
                    JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id
                    JOIN (SELECT extension_id, guild_id 
                          FROM GuildExtensions 
                          WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE ON TA.guild_id = GE.guild_id 
                    WHERE twitch_username = ?"""

                    results = self.ta_database_manager.database_manager.db_execute_select(
                        sql_find_message_id, args=[current_username])

                    new_message_embed = None

                    for result in results:
                        channel_id = result[0]
                        message_id = result[1]
                        team_twitch_alert_id = result[2]
                        custom_message = result[3]
                        channel_default_message = result[4]
                        channel = self.bot.get_channel(id=channel_id)
                        try:
                            # If no Alert is posted
                            if message_id is None:
                                if new_message_embed is None:
                                    if custom_message is not None:
                                        message = custom_message
                                    else:
                                        message = channel_default_message

                                    new_message_embed = await self.create_alert_embed(stream_data, message)

                                if new_message_embed is not None and channel is not None:
                                    new_message = await channel.send(embed=new_message_embed)

                                    sql_update_message_id = """
                                    UPDATE UserInTwitchTeam 
                                    SET message_id = ?
                                    WHERE team_twitch_alert_id = ?
                                    AND twitch_username = ?"""
                                    self.ta_database_manager.database_manager.db_execute_commit(
                                        sql_update_message_id,
                                        args=[new_message.id, team_twitch_alert_id, current_username])
                        except discord.errors.Forbidden as err:
                            logging.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                            sql_remove_invalid_channel = "DELETE FROM TwitchAlerts WHERE channel_id = ?"
                            self.ta_database_manager.database_manager.db_execute_commit(sql_remove_invalid_channel,
                                                                                        args=[channel.id])
            except Exception as err:
                logging.error(f"TwitchAlert: Team Loop error {err}")

        # Deals with remaining offline streams
        self.ta_database_manager.delete_all_offline_streams(True, usernames)
        time_diff = time.time() - start
        if time_diff > 5:
            logging.warning(f"TwitchAlert: Teams Loop Finished in > 5s | {time_diff}s")


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
    if game_info is None:
        embed.add_field(name="Playing", value="No Category")
    else:
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
        self.params = {'client_id': self.client_id,
                       'client_secret': self.client_secret,
                       'grant_type': 'client_credentials'}
        timeout = aiohttp.ClientTimeout(total=60)
        self.aiohttp = aiohttp.ClientSession(timeout=timeout)
        self.token = {}

    @property
    def base_headers(self):
        return {
            'Authorization': f'Bearer {self.token.get("access_token")}',
            'Client-ID': self.client_id
        }

    async def get_new_twitch_oauth(self):
        """
        Get a new OAuth2 token from twitch using client_id and client_secret
        :return: The new OAuth2 token
        """
        async with self.aiohttp.post('https://id.twitch.tv/oauth2/token', params=self.params) as response:
            if response.status > 399:
                logging.critical(f'TwitchAlert: Error {response.status} while getting Oauth token')
                self.token = {}

            response_json = await response.json()

            try:
                response_json['expires_in'] += time.time()
            except KeyError:
                # probably shouldn't need this, but catch just in case
                logging.warning('TwitchAlert: Failed to set token expiration time')

            self.token = response_json

            return self.token

    async def requests_get(self, url, headers=None, params=None):
        """
        Gets a response from a curl get request to the given url using headers of this object
        :param headers: the Headers required for the request, will use self.headers by default
        :param url: The URL to send the request to
        :param params: The parameters of the request
        :return: The response of the request
        """
        if self.token.get('expires_in', 0) <= time.time() + 1 or not self.token:
            await self.get_new_twitch_oauth()

        async with self.aiohttp.get(url=url, headers=headers if headers else self.base_headers, params=params) as \
                response:

            if response.status == 401:
                logging.info(f"TwitchAlert: {response.status}, getting new oauth and retrying")
                await self.get_new_twitch_oauth()
                return await self.requests_get(url, headers, params)
            elif response.status > 399:
                logging.warning(f'TwitchAlert: {response.status} while getting requesting URL:{url}')

            return await response.json()

    async def get_streams_data(self, usernames):
        """
        Gets all stream information from a list of given usernames
        :param usernames: The list of usernames
        :return: The JSON data of the request
        """
        url = 'https://api.twitch.tv/helix/streams?'

        next_hundred_users = usernames[:100]
        usernames = usernames[100:]
        result = (await self.requests_get(url + "user_login=" + "&user_login=".join(next_hundred_users))).get("data")

        while usernames:
            next_hundred_users = usernames[:100]
            usernames = usernames[100:]
            result += (await self.requests_get(url + "user_login=" + "&user_login=".join(next_hundred_users))).get(
                "data")

        return result

    async def get_user_data(self, username):
        """
        Gets the user information of a given user
        :param username: The display twitch username of the user
        :return: The JSON information of the user's data
        """
        url = 'https://api.twitch.tv/helix/users?login=' + username
        return (await self.requests_get(url)).get("data")[0]

    async def get_game_data(self, game_id):
        """
        Gets the game information of a given game
        :param game_id: The twitch game ID of a game
        :return: The JSON information of the game's data
        """
        if game_id != "":
            url = 'https://api.twitch.tv/helix/games?id=' + game_id
            game_data = await self.requests_get(url)
            return game_data.get("data")[0]
        else:
            return None

    async def get_team_users(self, team_id):
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        url = 'https://api.twitch.tv/kraken/teams/' + team_id
        return (
            await self.requests_get(url,
                                    headers={'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
                                    )).get("users")


class TwitchAlertDBManager:
    """
    A class for interacting with the Koala twitch database
    """

    def __init__(self, database_manager: KoalaDBManager.KoalaDBManager, bot_client: discord.client):
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
        sql_find_ta = "SELECT default_message FROM TwitchAlerts WHERE channel_id=?"
        message = self.database_manager.db_execute_select(sql_find_ta, args=[channel_id])
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
        self.database_manager.db_execute_commit(sql_insert_twitch_alert, args=[guild_id, channel_id, default_message])
        return default_message

    def get_default_message(self, channel_id):
        """
        Get the set default message for the twitch alert
        :param channel_id: The discord channel ID of the twitch Alert
        :return: The current default_message
        """
        sql_find_ta = "SELECT default_message FROM TwitchAlerts WHERE channel_id= ?"
        return self.database_manager.db_execute_select(sql_find_ta, args=[channel_id])

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
            self.database_manager.db_execute_commit(
                sql_insert_user_twitch_alert, args=[channel_id, str.lower(twitch_username), custom_message])
        else:
            sql_insert_user_twitch_alert = """
            INSERT INTO UserInTwitchAlert(channel_id, twitch_username) 
            VALUES(?, ?)
            """
            self.database_manager.db_execute_commit(
                sql_insert_user_twitch_alert, args=[channel_id, str.lower(twitch_username)])

    def remove_user_from_ta(self, channel_id, twitch_username):
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
        message_id = self.database_manager.db_execute_select(sql_get_message_id,
                                                             args=[twitch_username, channel_id])[0][0]
        if message_id is not None:
            asyncio.get_event_loop().create_task(self.delete_message(message_id, channel_id))
        sql_remove_entry = """DELETE FROM UserInTwitchAlert 
                               WHERE twitch_username = ? AND channel_id = ?"""
        self.database_manager.db_execute_commit(sql_remove_entry, args=[twitch_username, channel_id])

    async def delete_message(self, message_id, channel_id):
        """
        Deletes a given discord message
        :param message_id: discord message ID of the message to delete
        :param channel_id: discord channel ID which has the message
        :return:
        """
        try:
            message = await self.bot.get_channel(int(channel_id)).fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound as err:
            logging.warning(f"TwitchAlert: Message ID {message_id} does not exist, skipping \nError: {err}")
        except discord.errors.Forbidden as err:
            logging.warning(f"TwitchAlert: {err}  Channel ID: {channel_id}")
            sql_remove_invalid_channel = "DELETE FROM TwitchAlerts WHERE channel_id = ?"
            self.ta_database_manager.database_manager.db_execute_commit(sql_remove_invalid_channel, args=[channel_id])

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
            sql_insert_team_twitch_alert = """
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name, custom_message) 
            VALUES(?, ?, ?)
            """
            self.database_manager.db_execute_commit(
                sql_insert_team_twitch_alert, args=[channel_id, str.lower(twitch_team), custom_message])
        else:
            sql_insert_team_twitch_alert = """
            INSERT INTO TeamInTwitchAlert(channel_id, twitch_team_name) 
            VALUES(?, ?)
            """
            self.database_manager.db_execute_commit(
                sql_insert_team_twitch_alert, args=[channel_id, str.lower(twitch_team)])

    def remove_team_from_ta(self, channel_id, team_name):
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
        result = self.database_manager.db_execute_select(sql_get_team_alert_id, args=[team_name, channel_id])
        if not result:
            raise AttributeError("Team name not found")
        team_alert_id = result[0][0]
        sql_get_message_id = """SELECT UserInTwitchTeam.message_id
                                 FROM UserInTwitchTeam
                                 WHERE team_twitch_alert_id = ?"""
        message_ids = self.database_manager.db_execute_select(sql_get_message_id, args=[team_alert_id])
        if message_ids is not None:
            for message_id in message_ids:
                if message_id[0] is not None:
                    asyncio.get_event_loop().create_task(self.delete_message(message_id[0], channel_id))
        sql_remove_users = """DELETE FROM UserInTwitchTeam WHERE team_twitch_alert_id = ?"""
        sql_remove_team = """DELETE FROM TeamInTwitchAlert WHERE team_twitch_alert_id = ?"""
        self.database_manager.db_execute_commit(sql_remove_users, args=[team_alert_id])
        self.database_manager.db_execute_commit(sql_remove_team, args=[team_alert_id])

    async def update_team_members(self, twitch_team_id, team_name):
        """
        Users in a team are updated to ensure they are assigned to the correct team
        :param twitch_team_id: the team twitch alert id
        :param team_name: the name of the team
        :return:
        """
        if re.search(TWITCH_USERNAME_REGEX, team_name):
            users = await self.twitch_handler.get_team_users(team_name)
            for user in users:
                sql_add_user = """INSERT INTO UserInTwitchTeam(team_twitch_alert_id, twitch_username) 
                                   VALUES(?, ?)"""
                try:
                    self.database_manager.db_execute_commit(sql_add_user, args=[twitch_team_id, user.get("name")],
                                                            pass_errors=True)
                except KoalaDBManager.sqlite3.IntegrityError:
                    pass

    async def update_all_teams_members(self):
        """
        Updates all teams with the current team members
        :return:
        """
        sql_get_teams = """SELECT team_twitch_alert_id, twitch_team_name FROM TeamInTwitchAlert"""
        teams_info = self.database_manager.db_execute_select(sql_get_teams)
        for team_info in teams_info:
            await self.update_team_members(team_info[0], team_info[1])

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
            asyncio.get_event_loop().create_task(self.delete_message(result[1], result[0]))
        self.database_manager.db_execute_commit(sql_update_offline_streams, usernames)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TwitchAlert(bot))
    logging.info("TwitchAlert is ready.")
