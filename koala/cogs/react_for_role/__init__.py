from . import utils, db, models, cog, core, api
from .cog import ReactForRole


async def setup(bot):
    await cog.setup(bot)
    api.setup(bot)
