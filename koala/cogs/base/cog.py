#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
import datetime

# Futures

# Built-in/Generic Imports

# Libs

import discord
from discord import app_commands, Permissions
from discord.ext import commands, tasks
# Own modules
from discord.ext.commands import BadArgument

import koalabot
from koala import checks
from koala.transformers import DatetimeTransformer, ExtensionTransformer
from . import core
from .log import logger
from .utils import AUTO_UPDATE_ACTIVITY_DELAY



# Constants

# Variables


def convert_activity_type(argument):
    try:
        return discord.ActivityType[argument]
    except KeyError:
        raise BadArgument('Unknown activity type %s' % argument)


class BaseCog(commands.Cog, name='KoalaBot'):
    """
        A discord.py cog with general commands useful to managers of the bot and servers
    """
    owner_group = koalabot.owner_group
    cog_group = app_commands.Group(name="cog", description="control running cogs",
                                        parent=owner_group)
    activity_group = app_commands.Group(name="activity", description="Modify the activity of the bot",
                                        parent=owner_group)

    extension_group = app_commands.Group(name="extension", description="Enable or disable Koala functions",
                                         default_permissions=Permissions(administrator=True))

    def __init__(self, bot: commands.Bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        self._last_member = None
        self.started = False
        self.current_activity = None

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ran after all cogs have been started and bot is ready
        """
        core.activity_clear_current()
        await self.update_activity()
        self.update_activity.start()
        self.started = True
        logger.info("Bot is ready.")

    @activity_group.command(name="set", description="Change the activity of the bot")
    async def activity_set(self, interaction: discord.Interaction, activity: discord.ActivityType,
                           message: str, url: str = None):
        """
        Change the activity of the bot
        :param interaction:
        :param activity: The new activity of the bot
        :param message: The name of the activity
        :param url: url for streaming
        """
        await core.activity_set(activity, message, url, bot=self.bot)
        await interaction.response.send_message(f"I am now {activity.name} {message}", ephemeral=True)

    @activity_group.command(name="schedule", description="Schedule an activity")
    async def activity_schedule(self, interaction: discord.Interaction, activity: discord.ActivityType,
                                message: str,
                                start_time: app_commands.Transform[datetime.datetime, DatetimeTransformer],
                                end_time: app_commands.Transform[datetime.datetime, DatetimeTransformer],
                                url: str = None):
        """
        Schedule an activity
        :param interaction:
        :param activity: activity type (watching, playing etc.)
        :param message: message
        :param start_time: iso format start time
        :param end_time: iso format end time
        :param url: url
        """
        core.activity_schedule(activity, message, url, start_time, end_time)
        await interaction.response.send_message("Activity saved", ephemeral=True)

    @activity_group.command(name="list", description="List scheduled activities")
    async def activity_list(self, interaction: discord.Interaction, show_all: bool = False):
        """
        List scheduled activities
        :param interaction:
        :param show_all: false=future activities, true=all activities
        """
        activities = core.activity_list(show_all)
        result = "Activities:"
        for activity in activities:
            result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                    activity.stream_url, activity.message, activity.time_start,
                                                    activity.time_end)
        await interaction.response.send_message(result)

    @activity_group.command(name="remove", description="Remove a scheduled activity")
    async def activity_remove(self, interaction: discord.Interaction, activity_id: int):
        """
        Remove an existing activity
        :param interaction:
        :param activity_id: Activity ID
        """
        activity = core.activity_remove(activity_id)
        result = "Removed:"
        result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                activity.stream_url, activity.message, activity.time_start,
                                                activity.time_end)
        await interaction.response.send_message(result)

    @tasks.loop(minutes=AUTO_UPDATE_ACTIVITY_DELAY)
    async def update_activity(self):
        """
        Loop for updating the activity of the bot according to scheduled activities
        """
        try:
            await core.activity_set_current_scheduled(self.bot)
        except Exception as err:
            logger.error("Error in update_activity loop %s" % err, exc_info=err)

    @owner_group.command(name="ping", description="Ping the discord servers")
    async def ping(self, interaction: discord.Interaction):
        """
        Returns the ping of the bot
        :param interaction:
        """
        await interaction.response.send_message(await core.ping(self.bot), ephemeral=True)

    @app_commands.command(name="support", description="KoalaBot Support server link")
    async def support(self, interaction: discord.Interaction):
        """
        KoalaBot Support server link
        :param interaction:
        """
        await interaction.response.send_message(core.support_link())

    @app_commands.command(name="clear", description="Clear messages from this channel")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 1):
        """
        Clears a given number of messages from the given channel
        :param interaction:
        :param amount: Amount of lines to delete
        """
        await core.purge(self.bot, interaction.channel_id, amount)

    @cog_group.command(name="load", description="Load a cog")
    async def load_cog(self, interaction: discord.Interaction, extension: str):
        """
        Loads a cog from the cogs folder
        :param interaction:
        :param extension: The name of the cog
        """
        await interaction.response.send_message(await core.load_cog(self.bot, extension),
                                                ephemeral=True)

    @cog_group.command(name="unload", description="Unload a cog")
    async def unload_cog(self, interaction: discord.Interaction, extension: str):
        """
        Unloads a running cog
        :param interaction:
        :param extension: The name of the cog
        """
        await interaction.response.send_message(await core.unload_cog(self.bot, extension))

    @extension_group.command(name="enable", description="Enable a Koala extension")
    async def enable_koala_ext(self, interaction: discord.Interaction,
                               koala_extension: app_commands.Transform[str, ExtensionTransformer]):
        """
        Enables a koala extension onto a server, all grants all extensions
        :param interaction:
        :param koala_extension: The name of the koala
        """
        await interaction.response.send_message(
            embed=await core.enable_extension(self.bot, interaction.guild_id, koala_extension))

    @extension_group.command(name="disable", description="Disable a Koala extension")
    async def disable_koala_ext(self, interaction: discord.Interaction,
                                koala_extension: app_commands.Transform[str, ExtensionTransformer]):
        """
        Disables a koala extension onto a server
        :param interaction:
        :param koala_extension: The name of the koala
        """
        await interaction.response.send_message(
            embed=await core.disable_extension(self.bot, interaction.guild_id, koala_extension))

    @extension_group.command(name="list", description="List available Koala extensions")
    async def list_koala_ext(self, interaction: discord.Interaction):
        """
        Lists the enabled koala extensions of a server
        :param interaction:
        """
        await interaction.response.send_message(embed=await core.list_enabled_extensions(interaction.guild_id))

    @owner_group.command(name="version", description="KoalaBot version")
    async def version(self, interaction: discord.Interaction):
        """
        Get the version of KoalaBot
        :param interaction:
        """
        await interaction.response.send_message(core.get_version())


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.

    :param bot: the bot client for KoalaBot
    """
    await bot.add_cog(BaseCog(bot))
    logger.info("BaseCog is ready.")
