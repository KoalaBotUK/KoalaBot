from . import cog
from . import api
from .cog import BaseCog


async def setup(bot):
    await cog.setup(bot)
    api.setup(bot)
