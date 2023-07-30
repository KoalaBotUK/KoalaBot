from . import utils, core, twitch_handler, log, models
from .cog import TwitchAlert


async def setup(bot):
    from .env import TWITCH_KEY, TWITCH_SECRET
    await core.twitch_handler.setup(TWITCH_KEY, TWITCH_SECRET)
    await cog.setup(bot)
    # api.setup(bot)
