import discord
from discord.ext import commands#
import KoalaBot


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def hello(self, ctx, *, member: discord.Member = None):
        """Says hello"""
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}~'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar.'.format(member))
        self._last_member = member

    @commands.command()
    async def hi(self, ctx):
        """Says hi"""
        await ctx.send(f'Hi {ctx.author}')


def setup(bot: KoalaBot) -> None:
    """Load the Bot cog."""
    bot.add_cog(Greetings(bot))

