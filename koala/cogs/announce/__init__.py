from koala.cogs.announce import api

from . import db, log, models, utils
from .announce_message import AnnounceMessage
from .cog import Announce, setup


def setup(bot):
    cog.setup(bot)
    api.setup(bot)