from . import db, log, models, api, cog
from .cog import Verification


async def setup(bot):
    await cog.setup(bot)
    api.setup(bot)
