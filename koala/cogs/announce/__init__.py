from . import api, cog
from .cog import AnnounceCog


def setup(bot):
    cog.setup(bot)
    api.setup(bot)
