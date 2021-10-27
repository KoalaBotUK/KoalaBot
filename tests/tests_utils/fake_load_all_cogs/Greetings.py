"""
A test Cog to only be used for testing KoalaBot.load_all_cogs

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot


# Constants

# Variables


class Greetings(commands.Cog):
    """
    A cog used for tests that greets the user
    """

    def __init__(self, bot):
        """
        Initialises class variables
        :param bot: The client of the bot being used
        """
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def hello(self, ctx, *, member: discord.Member = None):
        """
        Says hello to the user
        :param ctx: context
        :param member: the member who sent the message
        """
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}~'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar.'.format(member))
        self._last_member = member

    @commands.command()
    async def hi(self, ctx):
        """
        Says hi to the user
        :param ctx: The context of the message
        """
        await ctx.send(f'Hi {ctx.author}')


def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    bot.add_cog(Greetings(bot))
