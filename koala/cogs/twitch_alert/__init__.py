from . import core, twitch_handler, log, models
from .cog import TwitchAlert
from .log import logger


async def setup(bot):
    from .env import TWITCH_KEY, TWITCH_SECRET
    if TWITCH_SECRET is None or TWITCH_KEY is None:
        logger.error("TwitchAlert not started. API keys not found in environment.")
    else:
        await core.twitch_handler.setup(TWITCH_KEY, TWITCH_SECRET)
        await cog.setup(bot)
        # api.setup(bot)
