from . import api
from . import cog
from .cog import Voting

async def setup(bot):
    await cog.setup(bot)
    api.setup(bot)