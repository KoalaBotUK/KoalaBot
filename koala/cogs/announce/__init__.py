from . import api, cog
from .cog import Announce, setup


def setup(bot):
    cog.setup(bot)
    api.setup(bot)
