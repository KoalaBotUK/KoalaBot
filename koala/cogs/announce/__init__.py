from . import api, cog
from .cog import Announce


def setup(bot):
    cog.setup(bot)
    api.setup(bot)
