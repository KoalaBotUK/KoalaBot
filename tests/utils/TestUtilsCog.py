import discord
from discord.ext import commands
import discord.ext.test as dpytest
import KoalaBot




class TestUtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.last_ctx = None

    @commands.command()
    async def store_ctx(self, ctx):
        """Says hi"""
        self.last_ctx = ctx
        # await ctx.send(f'Hi {ctx.author}')

    def get_last_ctx(self):
        return self.last_ctx


def setup(bot: KoalaBot) -> None:
    """Load the Bot cog."""
    bot.add_cog(TestUtilsCog(bot))

