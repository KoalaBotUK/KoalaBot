import pytest
from sqlalchemy import delete

from aiohttp import web
from discord.ext.commands import Bot

from koala.cogs.base.api import BaseEndpoint
from koala.cogs.base.models import ScheduledActivities
from koala.models import KoalaExtensions, GuildExtensions


@pytest.fixture(autouse=True)
def delete_tables(session):
    session.execute(delete(KoalaExtensions))
    session.execute(delete(GuildExtensions))
    session.execute(delete(ScheduledActivities))
    session.commit()

@pytest.fixture(autouse=True)
def setup_attributes(bot: Bot):
    app = web.Application()
    endpoint = BaseEndpoint(bot)
    endpoint.register(app)
    setattr(bot, "koala_web_app", app)