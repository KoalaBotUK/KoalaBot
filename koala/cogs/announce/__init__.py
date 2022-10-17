from . import api, cog, db, log, models, utils
from .announce_message import AnnounceMessage
from .cog import Announce, setup


def setup(bot):
    cog.setup(bot)
    api.setup(bot)