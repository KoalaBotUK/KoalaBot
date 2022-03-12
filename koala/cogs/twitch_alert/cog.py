# Futures

# Built-in/Generic Imports
import time
import re

# Own modules
import koalabot
from koalabot import COMMAND_PREFIX as CP
from koala.models import GuildExtensions
from koala.db import session_manager, insert_extension
from koala.colours import KOALA_GREEN
from koala.utils import error_embed, is_channel_in_guild
from .log import logger
from .models import UserInTwitchAlert, TwitchAlerts, UserInTwitchTeam, TeamInTwitchAlert
from .utils import create_live_embed
from .db import TwitchAlertDBManager
from .utils import DEFAULT_MESSAGE, TWITCH_USERNAME_REGEX, \
    LOOP_CHECK_LIVE_DELAY, REFRESH_TEAMS_DELAY, TEAMS_LOOP_CHECK_LIVE_DELAY
from .env import TWITCH_KEY, TWITCH_SECRET

# Libs
import discord
from discord.ext import commands, tasks
from sqlalchemy import select, or_, delete, and_, update, null


# Constants


# Variables

# Flask
from flask import Blueprint
twitch_alert_api = Blueprint('twitch_alert_api', __name__)

def twitch_is_enabled(ctx):
    """
    A command used to check if the guild has enabled twitch alert
    e.g. @commands.check(koalabot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(ctx, "TwitchAlert")
    except PermissionError:
        result = False

    return result


class TwitchAlert(commands.Cog):
    """
        A discord.py cog for alerting when someone goes live on twitch
    """

    def __init__(self, bot: discord.ext.commands.Bot):

        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        insert_extension("TwitchAlert", 0, True, True)
        self.ta_database_manager = TwitchAlertDBManager(bot)
        # self.ta_database_manager.translate_names_to_ids()
        self.loop_thread = None
        self.loop_team_thread = None
        self.running = False
        self.stop_loop = False
    
    @twitch_alert_api.route("/twitch_alert")
    def endpoint():
        return "twitch_alert test"

    @commands.check(koalabot.is_guild_channel)
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    @commands.group(name="twitch", short_doc="Group of commands for Twitch Alert functionality.")
    async def twitch_group(self, ctx: commands.Context):
        """
        Group of commands for Twitch Alert functionality.
        """
        pass

    @twitch_group.command(name="editMsg",
                          brief="Edit the default message used in a Twitch Alert notification",
                          usage=f"{CP}twitch editMsg <channel> [message]",
                          help=("""Edit the default message used in a Twitch Alert notification
                                
                                <channel>: The channel to be modified (e.g. #text-channel)
                                [message]: *optional* The default notification message for this text channel """
                                f"""(e.g. Your favourite stream is now live!)
                                
                                Example: {CP}twitch editMsg #text-channel \"Your favourite stream is now live!\""""))
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def edit_default_message(self, ctx, channel: discord.TextChannel, *default_live_message):
        """
        Edit the default message put in a Twitch Alert Notification
        :param ctx: The discord context of the command
        :param channel: The channel where the twitch alert is being used
        :param default_live_message: The default live message of users within this Twitch Alert,
        leave empty for program default
        :return:
        """
        channel_id = channel.id

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

    @twitch_group.command(name="viewMsg",
                          brief="Shows the current default message for Twitch Alerts",
                          usage=f"{CP}twitch viewMsg <channel>",
                          help=f"""Shows the current default message for Twitch Alerts
                          
                          <channel>: The channel to be modified (e.g. #text-channel)
                          
                          Example: {CP}twitch viewMsg #text-channel""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def view_default_message(self, ctx, channel: discord.TextChannel):
        """
        Shows the current default message for Twitch Alerts
        :param ctx: The discord context of the command
        :param channel: The channel where the twitch alert is being used
        leave empty for program default
        :return:
        """
        channel_id = channel.id

        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        # Creates a new Twitch Alert with the used guild ID and default message if provided
        default_message = self.ta_database_manager.get_default_message(channel_id)

        # Returns an embed with information altered
        new_embed = discord.Embed(title="Default Message", colour=KOALA_GREEN,
                                  description=f"Guild: {ctx.message.guild.id}\n"
                                              f"Channel: {channel_id}\n"
                                              f"Default Message: {default_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {new_id}")
        await ctx.send(embed=new_embed)

    @twitch_group.command(name="add",
                          brief="Add a Twitch user to a Twitch Alert",
                          usage=f"{CP}twitch add <username> <channel> [message]",
                          help=f"""Add a Twitch user to a Twitch Alert
                          
                          <username>: The twitch username to be added (e.g. thenuel)
                          <channel> : The channel to be modified (e.g. #text-channel)
                          [message] : *optional* The notification message for this user """
                          f"""(e.g. Your favourite streamer is now live!)
                          
                          Example: {CP}twitch add thenuel #text-channel \"Come watch us play games!\"""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def add_user_to_twitch_alert(self, ctx, twitch_username,
                                       channel: discord.TextChannel, *custom_live_message):
        """
        Add a Twitch user to a Twitch Alert
        :param ctx: The discord context of the command
        :param twitch_username: The Twitch Username of the user being added (lowercase)
        :param channel: The channel ID where the twitch alert is being used
        :param custom_live_message: the custom live message for this user's alert
        :return:
        """
        channel_id = channel.id
        twitch_username = str.lower(twitch_username)
        if not re.search(TWITCH_USERNAME_REGEX, twitch_username):
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

    @twitch_group.command(name="remove",
                          brief="Removes a user from a Twitch Alert",
                          usage=f"{CP}twitch remove <username> <channel>",
                          help=f"""Removes a user from a Twitch Alert
                          
                          <username>: The twitch username to be removed (e.g. thenuel)
                          <channel> : The channel to be modified (e.g. #text-channel)
                          
                          Example: {CP}twitch remove thenuel #text-channel""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def remove_user_from_twitch_alert(self, ctx, twitch_username, channel: discord.TextChannel):
        """
        Removes a user from a Twitch Alert
        :param ctx: the discord context
        :param twitch_username: The username of the user to be removed
        :param channel: The discord channel ID of the Twitch Alert
        :return:
        """

        channel_id = channel.id

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        await self.ta_database_manager.remove_user_from_ta(channel_id, twitch_username)
        # Response Message
        new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitch_username}")

        await ctx.send(embed=new_embed)

    @twitch_group.command(name="addTeam",
                          brief="Add a Twitch team to a Twitch Alert",
                          usage=f"{CP}twitch addTeam <team> <channel> [message]",
                          help=f"""Add a Twitch team to a Twitch Alert
                          
                          <team>    : The Twitch team to be added (e.g. thenuel)
                          <channel> : The channel to be modified (e.g. #text-channel)
                          [message] : *optional* The notification message for this user """
                          f"""(e.g. Your favourite streamer is now live!)
                          
                          Example: {CP}twitch addTeam thenuel #text-channel \"Come watch us play games!\"""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def add_team_to_twitch_alert(self, ctx, team_name, channel: discord.TextChannel, *custom_live_message):
        """
        Add a Twitch team to a Twitch Alert
        :param ctx: The discord context of the command
        :param team_name: The Twitch team being added (lowercase)
        :param channel: The channel ID where the twitch alert is being used
        :param custom_live_message: the custom live message for this team's alert
        :return:
        """
        channel_id = channel.id
        team_name = str.lower(team_name)

        if not re.search(TWITCH_USERNAME_REGEX, team_name):
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

    @twitch_group.command(name="removeTeam",
                          brief="Removes a team from a Twitch Alert",
                          usage=f"{CP}twitch removeTeam <team> <channel>",
                          help=f"""Removes a team from a Twitch Alert
                          
                          <team>    : The Twitch team to be added (e.g. thenuel)
                          <channel> : The channel to be modified (e.g. #text-channel)
                          
                          Example: {CP}twitch removeTeam thenuel #text-channel""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def remove_team_from_twitch_alert(self, ctx, team_name, channel: discord.TextChannel):
        """
        Removes a team from a Twitch Alert
        :param ctx: the discord context
        :param team_name: The Twitch team being added (lowercase)
        :param channel: The discord channel ID of the Twitch Alert
        :return:
        """

        channel_id = channel.id

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        await self.ta_database_manager.remove_team_from_ta(channel_id, team_name)
        # Response Message
        new_embed = discord.Embed(title="Removed Team from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"Team: {team_name}")

        await ctx.send(embed=new_embed)

    @twitch_group.command(name="list",
                          brief="Show twitch alerts in a channel",
                          usage=f"{CP}twitch list <channel>",
                          help=f"""Shows all current TwitchAlert users and teams in a channel
                          
                          <channel> : The discord channel (e.g. #text-channel)
                          
                          Example: {CP}twitch list #text-channel""")
    @commands.check(koalabot.is_admin)
    @commands.check(twitch_is_enabled)
    async def list_twitch_alert(self, ctx: discord.ext.commands.Context, channel: discord.TextChannel):
        """
        Shows all current TwitchAlert users and teams in a channel
        :param ctx:
        :param channel: The discord channel ID of the Twitch Alert
        """
        if not channel:
            channel = ctx.channel

        channel_id = channel.id

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
                users += f"{result.twitch_username}\n"
            embed.add_field(name=":bust_in_silhouette: Users", value=users)
        else:
            embed.add_field(name=":bust_in_silhouette: Users", value="None")

        results = self.ta_database_manager.get_teams_in_ta(channel_id)
        if results:
            teams = ""
            for result in results:
                teams += f"{result.twitch_team_name}\n"
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

    @tasks.loop(minutes=LOOP_CHECK_LIVE_DELAY)
    async def loop_check_live(self):
        """
        A loop that continually checks the live status of users and
        sends alerts when online, removing them when offline
        :return:
        """
        start = time.time()
        # logger.info("TwitchAlert: User Loop Started")
        sql_find_users = select(UserInTwitchAlert.twitch_username) \
            .join(TwitchAlerts, UserInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
            .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
            .where(or_(GuildExtensions.extension_id == 'TwitchAlert', GuildExtensions.extension_id == 'All'))
        # "SELECT twitch_username " \
        #              "FROM UserInTwitchAlert " \
        #              "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
        #              "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
        #              "WHERE extension_id = 'twitch_alert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id;"
        with session_manager() as session:
            users = session.execute(sql_find_users).all()

        usernames = [str.lower(user.twitch_username) for user in users]

        if not usernames:
            return

        user_streams = self.ta_database_manager.twitch_handler.get_streams_data(usernames)
        if user_streams is None:
            return

        # Deals with online streams
        for streams_details in user_streams:
            try:
                if streams_details.get('type') == "live":
                    current_username = str.lower(streams_details.get("user_login"))
                    old_len = len(usernames)
                    usernames.remove(current_username)
                    if len(usernames) == old_len:
                        logger.error(f"TwitchAlert: {streams_details.get('user_login')} not found in the user list")

                    sql_find_message_id = select(UserInTwitchAlert.channel_id,
                                                 UserInTwitchAlert.message_id,
                                                 UserInTwitchAlert.custom_message,
                                                 TwitchAlerts.default_message) \
                        .join(TwitchAlerts, UserInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
                        .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
                        .where(and_(and_(or_(GuildExtensions.extension_id == 'TwitchAlert',
                                             GuildExtensions.extension_id == 'All'),
                                         UserInTwitchAlert.twitch_username == current_username),
                                    UserInTwitchAlert.message_id == null()))
                    # "SELECT UserInTwitchAlert.channel_id, message_id, custom_message, default_message " \
                    # "FROM UserInTwitchAlert " \
                    # "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                    # "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                    # "WHERE extension_id = 'TwitchAlert' " \
                    # "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id " \
                    # "WHERE twitch_username = ?;"

                    results = session.execute(sql_find_message_id).all()

                    new_message_embed = None

                    for result in results:
                        channel_id = result.channel_id
                        message_id = result.message_id
                        custom_message = result.custom_message
                        channel_default_message = result.default_message

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
                                    sql_update_message_id = update(UserInTwitchAlert).where(and_(
                                        UserInTwitchAlert.channel_id == channel_id,
                                        UserInTwitchAlert.twitch_username == current_username)) \
                                        .values(message_id=new_message.id)
                                    session.execute(sql_update_message_id)
                                    session.commit()
                        except discord.errors.Forbidden as err:
                            logger.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                            sql_remove_invalid_channel = delete(TwitchAlerts).where(
                                TwitchAlerts.channel_id == channel.id)
                            session.execute(sql_remove_invalid_channel)
                            session.commit()

            except Exception as err:
                logger.error(f"TwitchAlert: User Loop error {err}")

        # Deals with remaining offline streams
        await self.ta_database_manager.delete_all_offline_streams(usernames)
        time_diff = time.time() - start
        if time_diff > 5:
            logger.warning(f"TwitchAlert: User Loop Finished in > 5s | {time_diff}s")

    async def create_alert_embed(self, stream_data, message):
        """
        Creates and sends an alert message
        :param stream_data: The twitch stream data to have in the message
        :param message: The custom message to be added as a description
        :return: The discord message id of the sent message
        """
        user_details = self.ta_database_manager.twitch_handler.get_user_data(
            stream_data.get("user_name"))[0]
        game_details = self.ta_database_manager.twitch_handler.get_game_data(
            stream_data.get("game_id"))
        return create_live_embed(stream_data, user_details, game_details, message)

    @tasks.loop(minutes=REFRESH_TEAMS_DELAY)
    async def loop_update_teams(self):
        start = time.time()
        # logger.info("TwitchAlert: Started Update Teams")
        self.ta_database_manager.update_all_teams_members()
        time_diff = time.time() - start
        if time_diff > 5:
            logger.warning(f"TwitchAlert: Teams updated in > 5s | {time_diff}s")

    @tasks.loop(minutes=TEAMS_LOOP_CHECK_LIVE_DELAY)
    async def loop_check_team_live(self):
        """
        A loop to repeatedly send messages if a member of a team is live, and remove it when they are not

        :return:
        """
        start = time.time()
        # logger.info("TwitchAlert: Team Loop Started")

        # Select all twitch users & team names where TwitchAlert is enabled
        sql_select_team_users = select(UserInTwitchTeam.twitch_username, TeamInTwitchAlert.twitch_team_name) \
            .join(TeamInTwitchAlert, UserInTwitchTeam.team_twitch_alert_id == TeamInTwitchAlert.team_twitch_alert_id) \
            .join(TwitchAlerts, TeamInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
            .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
            .where(or_(GuildExtensions.extension_id == 'TwitchAlert', GuildExtensions.extension_id == 'All'))
        with session_manager() as session:
            users_and_teams = session.execute(sql_select_team_users).all()
        # sql_select_team_users = "SELECT twitch_username, twitch_team_name " \
        #                         "FROM UserInTwitchTeam " \
        #                         "JOIN TeamInTwitchAlert TITA " \
        #                         "  ON UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id " \
        #                         "JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id " \
        #                         "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
        #                         "WHERE extension_id = 'TwitchAlert' " \
        #                         "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id "

        usernames = [str.lower(user.twitch_username) for user in users_and_teams]

        if not usernames:
            return

        streams_data = self.ta_database_manager.twitch_handler.get_streams_data(usernames)

        if streams_data is None:
            return
        # Deals with online streams
        for stream_data in streams_data:
            try:
                if stream_data.get('type') == "live":
                    current_username = str.lower(stream_data.get("user_login"))
                    old_len = len(usernames)
                    usernames.remove(current_username)
                    if len(usernames) == old_len:
                        logger.error(f"TwitchAlert: {stream_data.get('user_login')} not found in the user teams list")
                    sql_find_message_id = select(TeamInTwitchAlert.channel_id,
                                                 UserInTwitchTeam.message_id,
                                                 TeamInTwitchAlert.team_twitch_alert_id,
                                                 TeamInTwitchAlert.custom_message,
                                                 TwitchAlerts.default_message) \
                        .join(TeamInTwitchAlert,
                              UserInTwitchTeam.team_twitch_alert_id == TeamInTwitchAlert.team_twitch_alert_id) \
                        .join(TwitchAlerts, TeamInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
                        .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
                        .where(and_(and_(or_(GuildExtensions.extension_id == 'TwitchAlert',
                                             GuildExtensions.extension_id == 'All'),
                                         UserInTwitchTeam.twitch_username == current_username),
                                    UserInTwitchTeam.message_id == null()))

                    # sql_find_message_id = """
                    # SELECT TITA.channel_id, UserInTwitchTeam.message_id, TITA.team_twitch_alert_id, custom_message,
                    #   default_message
                    # FROM UserInTwitchTeam
                    # JOIN TeamInTwitchAlert TITA on UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id
                    # JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id
                    # JOIN (SELECT extension_id, guild_id
                    #       FROM GuildExtensions
                    #       WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE ON TA.guild_id = GE.guild_id
                    # WHERE twitch_username = ?"""

                    results = session.execute(sql_find_message_id).all()

                    new_message_embed = None

                    for result in results:
                        channel_id = result.channel_id
                        message_id = result.message_id
                        team_twitch_alert_id = result.team_twitch_alert_id
                        custom_message = result.custom_message
                        channel_default_message = result.default_message
                        channel: discord.TextChannel = self.bot.get_channel(id=channel_id)
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

                                    sql_update_message_id = update(UserInTwitchTeam) \
                                        .where(and_(UserInTwitchTeam.team_twitch_alert_id == team_twitch_alert_id,
                                                    UserInTwitchTeam.twitch_username == current_username)) \
                                        .values(message_id=new_message.id)
                                    session.execute(sql_update_message_id)
                                    session.commit()
                        except discord.errors.Forbidden as err:
                            logger.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                            sql_remove_invalid_channel = delete(TwitchAlerts).where(
                                TwitchAlerts.channel_id == channel.id)
                            session.execute(sql_remove_invalid_channel)
                            session.commit()
            except Exception as err:
                logger.error(f"TwitchAlert: Team Loop error {err}")

        # Deals with remaining offline streams
        await self.ta_database_manager.delete_all_offline_team_streams(usernames)
        time_diff = time.time() - start
        if time_diff > 5:
            logger.warning(f"TwitchAlert: Teams Loop Finished in > 5s | {time_diff}s")


def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    if TWITCH_SECRET is None or TWITCH_KEY is None:
        logger.error("TwitchAlert not started. API keys not found in environment.")
        insert_extension("TwitchAlert", 0, False, False)
    else:
        bot.add_cog(TwitchAlert(bot))
        logger.info("TwitchAlert is ready.")
