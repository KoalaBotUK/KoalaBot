from . import cog
from . import api
from .cog import BaseCog

def setup(bot):
    cog.setup(bot)
    api.setup(bot)
