#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

import inspect
# Built-in/Generic Imports
import io
import textwrap
import traceback
from contextlib import redirect_stdout

# Libs
from discord.ext import commands

# Own modules
import KoalaBot
from utils.KoalaColours import *


# Constants

# Variables


def new_discord_activity(activity, name):
    """
    This command takes an activity and name and returns the discord.Activity type for it

    Custom doesn't currently work
    koalabot.uk is added to the end of any activity
    :param activity: The new activity of the bot
    :param name: The name of the activity
    :return: The custom activity created
    """
    name = name + KoalaBot.KOALA_PLUG  # Added to every presence change, do not alter
    lower_activity = str.lower(activity)
    if lower_activity == "playing":
        activity_type = discord.ActivityType.playing
    elif lower_activity == "watching":
        activity_type = discord.ActivityType.watching
    elif lower_activity == "listening":
        activity_type = discord.ActivityType.listening
    elif lower_activity == "streaming":
        return discord.Activity(type=discord.ActivityType.streaming, name=name, url=KoalaBot.STREAMING_URL)
    elif lower_activity == "custom":
        return discord.Activity(type=discord.ActivityType.custom, name=name)
    else:
        raise SyntaxError(f"{activity} is not an activity")
    return discord.Activity(type=activity_type, name=name)


def list_ext_embed(guild_id):
    """
    Creates a discord embed of enabled and disabled extensions
    :param guild_id: The discord guild id of the server
    :return: The finished discord embed
    """
    embed = discord.Embed()
    embed.title = "Enabled extensions"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {guild_id}")
    enabled_results = KoalaBot.database_manager.get_enabled_guild_extensions(guild_id)
    all_results = KoalaBot.database_manager.get_all_available_guild_extensions(guild_id)
    enabled = ""
    disabled = ""
    for result in enabled_results:
        enabled += f"{result[0]}\n"
        try:
            all_results.remove((result[0],))
        except ValueError:
            pass
    for result in all_results:
        disabled += f"{result[0]}\n"
    if enabled != "":
        embed.add_field(name=":white_check_mark: Enabled", value=enabled)
    if disabled != "":
        embed.add_field(name=":negative_squared_cross_mark: Disabled", value=disabled)
    return embed


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
        if not self.started:  # Used to prevent changing activity every time the bot connects to discord servers
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
        await ctx.send(f"Pong! {round(self.bot.latency*1000)}ms")

    @commands.command(name="clear")
    @commands.check(KoalaBot.is_admin)
    async def clear(self, ctx, amount=2):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        """
        await ctx.channel.purge(limit=amount)

    @commands.command(name="loadCog", aliases=["load_cog"])
    @commands.check(KoalaBot.is_owner)
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        self.bot.load_extension(self.COGS_DIR.replace("/", ".")+f'.{extension}')
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
                KoalaBot.database_manager.give_guild_extension(guild_id, extension[0])
            embed = list_ext_embed(guild_id)
            embed.title = "All extensions enabled"

        else:
            KoalaBot.database_manager.give_guild_extension(guild_id, koala_extension)
            embed = list_ext_embed(guild_id)
            embed.title = koala_extension+" enabled"

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
                KoalaBot.database_manager.remove_guild_extension(guild_id, ext[0])
        elif (koala_extension,) not in all_ext:
            raise NotImplementedError(f"{koala_extension} is not an enabled extension")
        KoalaBot.database_manager.remove_guild_extension(guild_id, koala_extension)
        embed = list_ext_embed(guild_id)
        embed.title = koala_extension+" disabled"
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

    @commands.command(name="debug", hidden=True)
    @commands.check(KoalaBot.is_owner)
    async def debug(self, ctx, *, body: str):
        """Evaluates code."""

        blocked_words = ['.delete()', 'os', 'subprocess', 'history()', '("token")', "('token')"]
        for x in blocked_words:
            if x in body:
                return await ctx.send('Your code contains certain blocked words.')
        env = {
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'source': inspect.getsource,
        }

        env.update(globals())

        env.update(locals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()
        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def paginate(text: str):
            '''Simple generator that paginates text.'''
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != '', pages))

        try:
            exec(to_compile, env)
        except Exception as e:
            err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            return await ctx.message.add_reaction('\u2049')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(format(value))
            else:
                self.bot._last_result = ret
                out = await ctx.send(f'```py\n{value}{ret}\n```')

        if out:
            await ctx.message.add_reaction('\u2705')  # tick
        elif err:
            await ctx.message.add_reaction('\u2049')  # x
        else:
            await ctx.message.add_reaction('\u2708')

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(BaseCog(bot))
    print("BaseCog is ready.")

