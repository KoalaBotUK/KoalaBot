# Built-in/Generic Imports
import math
import time

# Own modules
import koalabot
from koala.colours import KOALA_GREEN
from koala.db import insert_extension
from koala.utils import extract_id, wait_for_message
from .announce_message import AnnounceMessage
from .db import AnnounceDBManager
from .log import logger
from .utils import ANNOUNCE_SEPARATION_DAYS, SECONDS_IN_A_DAY, MAX_MESSAGE_LENGTH

# Libs
import discord
from discord.ext import commands


def announce_is_enabled(guild):
    """
    A command used to check if the guild has enabled announce
    e.g. @commands.check(announce_is_enabled)

    :param guild: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(guild, "Announce")
    except PermissionError:
        result = False

    return result


class AnnounceMessage:
    """
    A class consisting the information about a announcement message
    """

    def __init__(self, title, message, thumbnail):
        """
        Initiate the message with default thumbnail, title and description
        :param title: The title of the announcement
        :param message: The message included in the announcement
        :param thumbnail: The logo of the server
        """
        self.title = title
        self.description = message
        self.thumbnail = thumbnail

    def set_title(self, title):
        """
        Changing the title of the announcement
        :param title: A string consisting the title
        :return:
        """
        self.title = title

    def set_description(self, message):
        """
        Changing the message in the announcement
        :param message: A string consisting the message
        :return:
        """
        self.description = message


class Announce:
    """
        Send DM announcements to certain roles and people.
    """

    def __init__(self, bot):
        self.bot = bot
        self.messages = {}
        self.roles = {}
        insert_extension("Announce", 0, True, True)
        self.announce_database_manager = AnnounceDBManager()

    def not_exceeded_limit(self, guild_id):
        """
        Check if enough days have passed for the user to use the announce function
        :return:
        """
        if self.announce_database_manager.get_last_use_date(guild_id):
            last_use = self.announce_database_manager.get_last_use_date(guild_id)
            if (time.time() - last_use) > ANNOUNCE_SEPARATION_DAYS * SECONDS_IN_A_DAY:
                return True
            else:
                return False

    def has_active_message(self, guild_id):
        """
        Check if a particular id has an active announcement pending announcement
        :param guild_id: The id of the guild of the command
        :return: Boolean of whether there is an active announcement or not
        """
        if guild_id in self.messages:
            return True
        else:
            return False

    def get_role_names(self, guild_id):
        """
        Get the names of the roles that are currently being announced
        :param guild_id: The id of the guild of the command
        :return: A list of strings consisting the names of the roles
        """
        if guild_id in self.roles:
            return self.roles[guild_id]
        else:
            return []

    def get_receivers(self, guild_id):
        """
        A function to get the receivers of a particular announcement
        :param roles: The list of roles in the guild
        :param guild_id: The id of the guild
        :return: All the receivers of the announcement
        """
        receivers = []
        if guild_id in self.roles:
            roles = self.roles[guild_id]
            for role in roles:
                for member in role.members:
                    receivers.append(member)
        return receivers

    def receiver_msg(self, guild):
        """
        A function to create a string message about receivers
        :param guild: The guild of the bot
        :return: A string message about receivers
        """
        if not self.roles[guild.id]:
            return f"You are currently sending to Everyone and there are {str(len(guild.members))} receivers"
        else:
            receivers = self.get_receivers(guild.id)
            return f"You are currently sending to {str(len(self.roles[guild.id]))} roles and {str(len(receivers))} receivers"

    def construct_embed(self, guild: discord.Guild):
        """
        Constructing an embedded message from the information stored in the manager
        :param guild: The the guild
        :return: An embedded message for the announcement
        """
        message = self.messages[guild.id]
        embed: discord.Embed = discord.Embed(title=message.title,
                                             description=message.description, colour=KOALA_GREEN)
        embed.set_author(name="Announcement from " + guild.name)
        if message.thumbnail != 'https://cdn.discordapp.com/':
            embed.set_thumbnail(url=message.thumbnail)
        return embed

    @commands.check(announce_is_enabled)
    @commands.group(name="announce")
    async def announce(self, ctx):
        """
        The main command for the announce cog
        :param ctx: The context of the command
        :return:
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                f"{ctx.author.mention}, please use `{ctx.prefix}announce help` to see the help for this command")
