from . import utils, db, models, cog, core
from .cog import ReactForRole, setup

def setup(bot):
    cog.setup(bot)