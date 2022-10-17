import pytest
from aiohttp import web
from discord.ext.commands import Bot

from koala.cogs.announce.api import AnnounceEndpoint


@pytest.fixture(autouse=True)
def setup_attributes(bot: Bot):
    app = web.Application()
    endpoint = AnnounceEndpoint(bot)
    endpoint.register(app)
    setattr(bot, "koala_web_app", app)