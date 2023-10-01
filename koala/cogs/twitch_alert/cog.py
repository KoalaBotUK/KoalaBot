# Futures

import re
# Built-in/Generic Imports
import time

# Libs
import discord
from discord import app_commands
from discord.ext import commands, tasks

# Own modules
import koalabot
from koala.colours import KOALA_GREEN
from koala.db import insert_extension
from koala.utils import error_embed, is_channel_in_guild
from . import core
from .db import TwitchAlertDBManager
from .env import TWITCH_KEY, TWITCH_SECRET
from .log import logger
from .utils import TWITCH_USERNAME_REGEX, \
    LOOP_CHECK_LIVE_DELAY, REFRESH_TEAMS_DELAY, TEAMS_LOOP_CHECK_LIVE_DELAY
from ... import checks


# Constants


# Variables

class TwitchUsernameTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        twitch_username = str.lower(value)
        if not re.search(TWITCH_USERNAME_REGEX, twitch_username):
            interaction.data[checks.FAILURE_DESC_ATTR] = \
                "The given twitch_username is not a valid username (please use lowercase)"
            raise ValueError(interaction.data[checks.FAILURE_DESC_ATTR])
        return twitch_username


@app_commands.guilds(590643624358969350)
@app_commands.default_permissions(administrator=True)
class TwitchAlert(commands.GroupCog, group_name="twitch", group_description="TwitchAlert"):
    """
        A discord.py cog for alerting when someone goes live on twitch
    """
    message_group = app_commands.Group(name="message", description="View or modify the message sent with an alert")
    user_group = app_commands.Group(name="user", description="Add or remove user twitch alerts")
    team_group = app_commands.Group(name="team", description="Add or remove team twitch alerts")

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

    @message_group.command(name="edit",
                           description="Edit the default message used in a Twitch Alert notification")
    async def edit_default_message(self, interaction: discord.Interaction, channel: discord.TextChannel = None,
                                   default_live_message: app_commands.Range[str, None, 1000] = None):
        """
        Edit the default message used in a Twitch Alert notification

        <channel>: The channel to be modified (e.g. #text-channel)
        [message]: *optional* The default notification message for this text channel
        (e.g. Your favourite stream is now live!)

        Example: /twitch editMsg #text-channel "Your favourite stream is now live!"

        :param interaction: The discord interaction of the command
        :param channel: The channel where the twitch alert is being used
        :param default_live_message: The default live message of users within this Twitch Alert,
        leave empty for program default
        :return:
        """
        channel = channel if channel else interaction.channel

        # Creates a new Twitch Alert with the used guild ID and default message if provided
        default_message = core.new_ta(channel.guild.id, channel.id, default_live_message,
                                                          replace=True)

        # Returns an embed with information altered
        new_embed = discord.Embed(title="Default Message Edited", colour=KOALA_GREEN,
                                  description=f"Guild: {channel.guild.id}\n"
                                              f"Channel: {channel.id}\n"
                                              f"Default Message: {default_message}")
        await interaction.response.send_message(embed=new_embed)

    @message_group.command(name="view",
                           description="Shows the current default message for Twitch Alerts")
    async def view_default_message(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """
        Shows the current default message for Twitch Alerts

        <channel>: The channel to be modified (e.g. #text-channel)
        Example: /twitch viewMsg #text-channel

        :param interaction: The discord interaction of the command
        :param channel: The channel where the twitch alert is being used
        leave empty for program default
        :return:
        """
        channel = channel if channel else interaction.channel

        # Creates a new Twitch Alert with the used guild ID and default message if provided
        default_message = self.ta_database_manager.get_default_message(channel.id)

        # Returns an embed with information altered
        new_embed = discord.Embed(title="Default Message", colour=KOALA_GREEN,
                                  description=f"Guild: {channel.guild.id}\n"
                                              f"Channel: {channel.id}\n"
                                              f"Default Message: {default_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {new_id}")
        await interaction.response.send_message(embed=new_embed)

    @user_group.command(name="add",
                        description="Add a Twitch user to a Twitch Alert")
    async def add_user_to_twitch_alert(self, interaction: discord.Interaction,
                                       twitch_username: app_commands.Transform[str, TwitchUsernameTransformer],
                                       channel: discord.TextChannel = None,
                                       custom_live_message: app_commands.Range[str, None, 1000] = None):
        """
        Add a Twitch user to a Twitch Alert

          <username>: The twitch username to be added (e.g. thenuel)
          <channel> : The channel to be modified (e.g. #text-channel)
          [message] : *optional* The notification message for this user
          (e.g. Your favourite streamer is now live!)

          Example: /twitch add thenuel #text-channel "Come watch us play games!"

        :param interaction: The discord interaction of the command
        :param twitch_username: The Twitch Username of the user being added (lowercase)
        :param channel: The channel ID where the twitch alert is being used
        :param custom_live_message: the custom live message for this user's alert
        :return:
        """
        channel = channel if channel else interaction.channel
        default_message = core.new_ta(channel.guild.id, channel.id)
        custom_live_message = custom_live_message if custom_live_message else default_message

        core.add_user_to_ta(channel.id, twitch_username, custom_live_message, channel.guild.id)

        # Response Message
        new_embed = discord.Embed(title="Added User to Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"User: {twitch_username}\n"
                                              f"Message: {custom_live_message}")

        await interaction.response.send_message(embed=new_embed)

    @user_group.command(name="remove",
                        description="Removes a user from a Twitch Alert")
    async def remove_user_from_twitch_alert(self, interaction: discord.Interaction,
                                            twitch_username: app_commands.Transform[str, TwitchUsernameTransformer],
                                            channel: discord.TextChannel = None):
        """
        Removes a user from a Twitch Alert

          <username>: The twitch username to be removed (e.g. thenuel)
          <channel> : The channel to be modified (e.g. #text-channel)

          Example: /twitch remove thenuel #text-channel

        :param interaction: the discord interaction
        :param twitch_username: The username of the user to be removed
        :param channel: The discord channel ID of the Twitch Alert
        :return:
        """
        channel = channel if channel else interaction.channel
        await core.remove_user_from_ta(self.bot, channel.id, twitch_username)
        # Response Message
        new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"User: {twitch_username}")

        await interaction.response.send_message(embed=new_embed)

    @team_group.command(name="add",
                        description="Add a Twitch team to a Twitch Alert")
    async def add_team_to_twitch_alert(self, interaction: discord.Interaction,
                                       team_name: app_commands.Transform[str, TwitchUsernameTransformer],
                                       channel: discord.TextChannel = None,
                                       custom_live_message: app_commands.Range[str, None, 1000] = None):
        """
        Add a Twitch team to a Twitch Alert

          <team>    : The Twitch team to be added (e.g. thenuel)
          <channel> : The channel to be modified (e.g. #text-channel)
          [message] : *optional* The notification message for this user
          (e.g. Your favourite streamer is now live!)

          Example: /twitch addTeam thenuel #text-channel "Come watch us play games!"
        :param interaction: The discord interaction of the command
        :param team_name: The Twitch team being added (lowercase)
        :param channel: The channel ID where the twitch alert is being used
        :param custom_live_message: the custom live message for this team's alert
        :return:
        """
        channel = channel if channel else interaction.channel

        default_message = core.new_ta(channel.guild.id, channel.id)
        custom_live_message = custom_live_message if custom_live_message else default_message

        core.add_team_to_ta(channel.id, team_name, custom_live_message, channel.guild.id)

        # Response Message
        new_embed = discord.Embed(title="Added Team to Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"Team: {team_name}\n"
                                              f"Message: {custom_live_message}")
        # new_embed.set_footer(text=f"Twitch Alert ID: {channel_id}")
        await interaction.response.send_message(embed=new_embed)

    @team_group.command(name="remove",
                        description="Removes a team from a Twitch Alert")
    async def remove_team_from_twitch_alert(self, interaction: discord.Interaction,
                                            team_name: app_commands.Transform[str, TwitchUsernameTransformer],
                                            channel: discord.TextChannel = None):
        """
        Removes a team from a Twitch Alert

          <team>    : The Twitch team to be added (e.g. thenuel)
          <channel> : The channel to be modified (e.g. #text-channel)

          Example: /twitch removeTeam thenuel #text-channel
        :param interaction: the discord interaction
        :param team_name: The Twitch team being added (lowercase)
        :param channel: The discord channel ID of the Twitch Alert
        :return:
        """
        channel = channel if channel else interaction.channel
        await core.remove_team_from_ta(self.bot, channel.id, team_name)
        # Response Message
        new_embed = discord.Embed(title="Removed Team from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"Team: {team_name}")

        await interaction.response.send_message(embed=new_embed)

    @app_commands.command(name="list",
                          description="Show twitch alerts in a channel")
    async def list_twitch_alert(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """
        Shows all current TwitchAlert users and teams in a channel
        :param interaction:
        :param channel: The discord channel ID of the Twitch Alert
        """
        channel = channel if channel else interaction.channel

        if not is_channel_in_guild(self.bot, interaction.guild_id, channel.id):
            await interaction.response.send_message(
                embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return
        embed = discord.Embed()
        embed.title = "Twitch Alerts"
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Channel ID: {channel.id}")

        results = core.get_users_in_ta(channel.id)
        if results:
            users = ""
            for result in results:
                users += f"{result.twitch_username}\n"
            embed.add_field(name=":bust_in_silhouette: Users", value=users)
        else:
            embed.add_field(name=":bust_in_silhouette: Users", value="None")

        results = core.get_teams_in_ta(channel.id)
        if results:
            teams = ""
            for result in results:
                teams += f"{result.twitch_team_name}\n"
            embed.add_field(name=":busts_in_silhouette: Teams", value=teams)
        else:
            embed.add_field(name=":busts_in_silhouette: Teams", value="None")

        await interaction.response.send_message(embed=embed)

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
        try:
            await core.create_user_alerts(self.bot, self.ta_database_manager)
        except Exception as err:
            logger.error("Twitch user live loop error: ", exc_info=err)

    @tasks.loop(minutes=REFRESH_TEAMS_DELAY)
    async def loop_update_teams(self):
        start = time.time()
        # logger.info("TwitchAlert: Started Update Teams")
        await self.ta_database_manager.update_all_teams_members()
        time_diff = time.time() - start
        if time_diff > 5:
            logger.warning(f"TwitchAlert: Teams updated in > 5s | {time_diff}s")

    @tasks.loop(minutes=TEAMS_LOOP_CHECK_LIVE_DELAY)
    async def loop_check_team_live(self):
        """
        A loop to repeatedly send messages if a member of a team is live, and remove it when they are not

        :return:
        """
        try:
            await core.create_team_alerts(self.bot, self.ta_database_manager)
        except Exception as err:
            logger.error("Twitch team live loop error: ", exc_info=err)


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    if TWITCH_SECRET is None or TWITCH_KEY is None:
        insert_extension("TwitchAlert", 0, False, False)
    else:
        await bot.add_cog(TwitchAlert(bot))
        logger.info("TwitchAlert is ready.")
