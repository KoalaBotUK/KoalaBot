from . import cog
from . import api
from .cog import AnnounceCog

def setup(bot):
    cog.setup(bot)
    api.setup(bot)
