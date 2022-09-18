#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
from typing import List

import discord
from discord.ext import commands, tasks

# Own modules
from discord.ext.commands import BadArgument
from koala.utils import convert_iso_datetime

import koalabot
from koala.db import add_admin_roles, remove_admin_role, get_admin_roles
from . import core
from .utils import AUTO_UPDATE_ACTIVITY_DELAY
from .log import logger

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

    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        self._last_member = None
        self.started = False
        self.current_activity = None
        self.COGS_PACKAGE = koalabot.COGS_PACKAGE

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

    @commands.group(name="activity")
    @commands.check(koalabot.is_owner)
    async def activity_group(self, ctx: commands.Context):
        """
        Group of commands for activity functionality.
        :param ctx: Context of the command
        :return:
        """

    @activity_group.command(name="set")
    @commands.check(koalabot.is_owner)
    async def activity_set(self, ctx, new_activity: convert_activity_type, name: str, url: str = None):
        """
        Change the activity of the bot
        :param ctx: Context of the command
        :param new_activity: The new activity of the bot
        :param name: The name of the activity
        :param url: url for streaming
        """
        await core.activity_set(new_activity, name, url, bot=self.bot)
        await ctx.send(f"I am now {new_activity.name} {name}")

    @activity_group.command(name="schedule")
    @commands.check(koalabot.is_owner)
    async def activity_schedule(self, ctx, new_activity: convert_activity_type, message: str,
                                start_time: convert_iso_datetime, end_time: convert_iso_datetime, url: str = None):
        """
        Schedule an activity
        :param ctx: Context of the command
        :param new_activity: activity type (watching, playing etc.)
        :param message: message
        :param start_time: iso format start time
        :param end_time: iso format end time
        :param url: url
        """
        core.activity_schedule(new_activity, message, url, start_time, end_time)
        await ctx.send("Activity saved")

    @activity_group.command(name="list")
    @commands.check(koalabot.is_owner)
    async def activity_list(self, ctx, show_all: bool = False):
        """
        List scheduled activities
        :param ctx: Context of the command
        :param show_all: false=future activities, true=all activities
        """
        activities = core.activity_list(show_all)
        result = "Activities:"
        for activity in activities:
            result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                    activity.stream_url, activity.message, activity.time_start,
                                                    activity.time_end)
        await ctx.send(result)

    @activity_group.command(name="remove")
    @commands.check(koalabot.is_owner)
    async def activity_remove(self, ctx, activity_id: int):
        """
        Remove an existing activity
        :param ctx: Context of the command
        :param activity_id: Activity ID
        """
        activity = core.activity_remove(activity_id)
        result = "Removed:"
        result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                activity.stream_url, activity.message, activity.time_start,
                                                activity.time_end)
        await ctx.send(result)

    @tasks.loop(minutes=AUTO_UPDATE_ACTIVITY_DELAY)
    async def update_activity(self):
        """
        Loop for updating the activity of the bot according to scheduled activities
        """
        try:
            await core.activity_set_current_scheduled(self.bot)
        except Exception as err:
            logger.error("Error in update_activity loop %s" % err, exc_info=err)

    @commands.command()
    async def ping(self, ctx):
        """
        Returns the ping of the bot
        :param ctx: Context of the command
        """
        await ctx.send(await core.ping(self.bot))

    @commands.command()
    async def support(self, ctx):
        """
        KoalaBot Support server link
        :param ctx: Context of the command
        """
        await ctx.send(core.support_link())

    @commands.command(name="clear")
    @commands.check(koalabot.is_admin)
    async def clear(self, ctx, amount: int = 1):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        """
        await core.purge(self.bot, ctx.channel.id, amount)

    @commands.command(name="loadCog", aliases=["load_cog"])
    @commands.check(koalabot.is_owner)
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        await ctx.send(await core.load_cog(self.bot, extension, self.COGS_PACKAGE))

    @commands.command(name="unloadCog", aliases=["unload_cog"])
    @commands.check(koalabot.is_owner)
    async def unload_cog(self, ctx, extension):
        """
        Unloads a running cog
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        await ctx.send(await core.unload_cog(self.bot, extension, self.COGS_PACKAGE))

    @commands.command(name="enableExt", aliases=["enable_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def enable_koala_ext(self, ctx, koala_extension):
        """
        Enables a koala extension onto a server, all grants all extensions
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        await ctx.send(embed=await core.enable_extension(self.bot, ctx.message.guild.id, koala_extension))

    @commands.command(name="disableExt", aliases=["disable_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def disable_koala_ext(self, ctx, koala_extension):
        """
        Disables a koala extension onto a server
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        await ctx.send(embed=await core.disable_extension(self.bot, ctx.message.guild.id, koala_extension))

    @commands.command(name="listExt", aliases=["list_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def list_koala_ext(self, ctx):
        """
        Lists the enabled koala extensions of a server
        :param ctx: Context of the command
        """
        await ctx.send(embed=await core.list_enabled_extensions(ctx.message.guild.id))

    @commands.command(name="version")
    @commands.check(koalabot.is_owner)
    async def version(self, ctx):
        """
        Get the version of KoalaBot
        """
        await ctx.send(core.get_version())
    def get_admin_roles(self, guild: discord.Guild) -> List[discord.Role]:
        """
          Returns list of all roles that can use admin bot permissions in a guild
          :param guild: Guild that is checked
        """
        role_ids = get_admin_roles(guild.id)
        if not role_ids:
            return []
        roles = [guild.get_role(role_id) for role_id in role_ids]
        return roles

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """
          Listens for roles being deleted in a guild. On a role being deleted, it automatically removes the role from the
          database table.

          :param role: Role that was deleted from the guild
        """
        admin = get_admin_roles(role.guild.id)
        if role.id in admin:
            remove_admin_role(role.guild.id, role.id)

    @commands.check(koalabot.is_admin)
    @commands.command(name="listAdminRoles",
                      aliases=["list_admin_roles", "listBotRoles", "list_bot_roles"])
    async def list_admin_roles(self, ctx: commands.Context):
        """
        Lists the admin roles. Requires admin permissions to use.

        :param ctx: Context of the command
        :return: Sends a message with the mentions of the roles that are protected in a guild
        """
        roles = self.get_admin_roles(ctx.guild)
        msg = "Roles who have admin permissions are:\r\n"
        for role in roles:
            msg += f"{role.mention}\n"
        await ctx.send(msg[:-1])

    @commands.check(koalabot.is_owner)
    @commands.command(name="addAdminRole", alias=["add_admin_role",
                                                  "addAdministratorRole", "add_administrator_role",
                                                  "addBotRole", "add_bot_role"])
    async def add_admin_role(self, ctx: commands.Context, *, role_str: str):
        """
        Allow a role, via ID, mention or name to the list of roles allowed to have admin bot permissions.
        Needs admin permissions to use.

        :param ctx: Context of the command
        :param role_str: The role to add (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        admin_roles = get_admin_roles(ctx.guild.id)
        if role.id in admin_roles:
            await ctx.send(f"{role.mention} already has admin permissions.")
        else:
            add_admin_roles(ctx.guild.id, role.id)
            await ctx.send(f"Added {role.mention} to the list of roles allowed to have a bot admin permissions.")


    @commands.check(koalabot.is_owner)
    @commands.command(name="removeAdminRole",
                      aliases=["remove_admin_role", "removeBotRole", "remove_bot_role"])
    async def remove_admin_role(self, ctx: commands.Context, *, role_str: str):
        """
        Removes a role, via ID, mention or name, from the list of roles allowed use bot admin commands.

        :param ctx: Context of the command
        :param role_str: The role to remove (ID, name or mention)
        """
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
        admin_roles = get_admin_roles(ctx.guild.id)
        if role.id not in admin_roles:
            await ctx.send(f"{role.mention} doesn't have admin permissions.")
        else:
            remove_admin_role(ctx.guild.id, role.id)
            await ctx.send(f"Removed {role.mention} from the list of roles allowed to have a bot admin commands.")

def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.

    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(BaseCog(bot))
    logger.info("BaseCog is ready.")
