#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
from discord.ext import commands

# Own modules
import KoalaBot
from .utils import new_discord_activity, list_ext_embed

# Constants

# Variables


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
        self.COGS_DIR = KoalaBot.COGS_DIR

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ran after all cogs have been started and bot is ready
        """
        await self.bot.change_presence(activity=new_discord_activity("playing", f"{KoalaBot.COMMAND_PREFIX}help"))
        self.started = True
        print("Bot is ready.")

    @commands.command(name="activity", aliases=["change_activity"])
    @commands.check(KoalaBot.is_owner)
    async def change_activity(self, ctx, new_activity, name):
        """
        Change the activity of the bot
        :param ctx: Context of the command
        :param new_activity: The new activity of the bot
        :param name: The name of the activity
        """
        if str.lower(new_activity) in ["playing", "watching", "listening", "streaming"]:
            await self.bot.change_presence(activity=new_discord_activity(new_activity, name))
            await ctx.send(f"I am now {new_activity} {name}")
        else:
            await ctx.send("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")

    @commands.command()
    async def ping(self, ctx):
        """
        Returns the ping of the bot
        :param ctx: Context of the command
        """
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def support(self, ctx):
        """
        KoalaBot Support server link
        :param ctx: Context of the command
        """
        await ctx.send(f"Join our support server for more help! https://discord.gg/5etEjVd")

    @commands.command(name="clear")
    @commands.check(KoalaBot.is_admin)
    async def clear(self, ctx, amount: int = 1):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        """
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(name="loadCog", aliases=["load_cog"])
    @commands.check(KoalaBot.is_owner)
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        self.bot.load_extension(self.COGS_DIR.replace("/", ".") + f'.{extension}')
        await ctx.send(f'{extension} Cog Loaded')

    @commands.command(name="unloadCog", aliases=["unload_cog"])
    @commands.check(KoalaBot.is_owner)
    async def unload_cog(self, ctx, extension):
        """
        Unloads a running cog
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        if extension == "BaseCog":
            await ctx.send("Sorry, you can't unload the base cog")
        else:
            self.bot.unload_extension(self.COGS_DIR.replace("/", ".") + f'.{extension}')
            await ctx.send(f'{extension} Cog Unloaded')

    @commands.command(name="enableExt", aliases=["enable_koala_ext"])
    @commands.check(KoalaBot.is_admin)
    async def enable_koala_ext(self, ctx, koala_extension):
        """
        Enables a koala extension onto a server, all grants all extensions
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        guild_id = ctx.message.guild.id

        if koala_extension.lower() in ["all"]:
            available_extensions = KoalaBot.database_manager.get_all_available_guild_extensions(guild_id)
            for extension in available_extensions:
                KoalaBot.database_manager.give_guild_extension(guild_id, extension)
            embed = list_ext_embed(guild_id)
            embed.title = "All extensions enabled"

        else:
            KoalaBot.database_manager.give_guild_extension(guild_id, koala_extension)
            embed = list_ext_embed(guild_id)
            embed.title = koala_extension + " enabled"

        await ctx.send(embed=embed)

    @commands.command(name="disableExt", aliases=["disable_koala_ext"])
    @commands.check(KoalaBot.is_admin)
    async def disable_koala_ext(self, ctx, koala_extension):
        """
        Disables a koala extension onto a server
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        guild_id = ctx.message.guild.id
        all_ext = KoalaBot.database_manager.get_enabled_guild_extensions(guild_id)
        if koala_extension.lower() in ["all"]:
            for ext in all_ext:
                KoalaBot.database_manager.remove_guild_extension(guild_id, ext)
        elif koala_extension not in all_ext:
            raise NotImplementedError(f"{koala_extension} is not an enabled extension")
        KoalaBot.database_manager.remove_guild_extension(guild_id, koala_extension)
        embed = list_ext_embed(guild_id)
        embed.title = koala_extension + " disabled"
        await ctx.send(embed=embed)

    @commands.command(name="listExt", aliases=["list_koala_ext"])
    @commands.check(KoalaBot.is_admin)
    async def list_koala_ext(self, ctx):
        """
        Lists the enabled koala extensions of a server
        :param ctx: Context of the command
        """
        guild_id = ctx.message.guild.id
        embed = list_ext_embed(guild_id)

        await ctx.send(embed=embed)

    @commands.command(name="version")
    @commands.check(KoalaBot.is_owner)
    async def version(self, ctx):
        """
        Get the version of KoalaBot
        """
        await ctx.send("version: "+KoalaBot.__version__)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(BaseCog(bot))
    print("BaseCog is ready.")
