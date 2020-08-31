#!/usr/bin/env python

"""
Koala Bot Intro Message Cog Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import re
# Libs
import asyncio

import discord
from discord.ext import commands
import emoji

# Own modules
import KoalaBot
from utils import KoalaDBManager

# Constants
UNICODE_EMOJI_REGEXP: re.Pattern = emoji.get_emoji_regexp()
CUSTOM_EMOJI_REGEXP: re.Pattern = re.compile("^<a:.+?:\d+>|<:.+?:\d+>$")


class ReactForRole(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("ReactForRole", 0, True, True)

    @commands.group(name="reactForRole", aliases=["rfr", "react_for_role", "ReactForRole"])
    async def react_for_role_group(self, ctx: commands.Context):
        return

    @react_for_role_group.command(name="addRole")
    async def rfr_add_role_to_msg(self, ctx: commands.Context, *, role_str):
        role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)

        return

    def wait_for_message(self, bot: discord.Client, ctx: commands.Context):
        return

    def get_first_emoji_from_msg(self, ctx: commands.Context):
        msg: discord.Message = ctx.message
        content = msg.content
        # First check for a unicode emoji in the message
        search_result = UNICODE_EMOJI_REGEXP.search(content)
        if not search_result:
            search_result = CUSTOM_EMOJI_REGEXP.search(content)
            if not search_result:
                await ctx.send("No emotes found in your message. Please restart the command.")
                return None
        emoji_str = search_result.group()
        try:
            discord_emoji = commands.EmojiConverter().convert(ctx, emoji_str)
            return discord_emoji
        except commands.CommandError:
            await ctx.send(
                "An error occurred when trying to get the emoji. Please contact the bot developers for support.")
            return None
        except commands.BadArgument:
            await ctx.send("Couldn't get the emoji you used - is it from this server or a server I'm in?")
            return None
