import datetime
import inspect
import json
from collections import OrderedDict

from aiohttp import web
from aiohttp.http_exceptions import HttpBadRequest
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp.web import Request, Response, Application
from discord.ext.commands import Bot

from koala.cogs.base.log import logger
from koala.models import BaseModel
from koala.rest.api import parse_request

BASE_ENDPOINT = 'base'
ACTIVITY_ENDPOINT = 'activity'


class BaseEndpoint:
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        app.add_routes([web.get('/{endpoint}'.format(endpoint=ACTIVITY_ENDPOINT), self.get_activities)])
        return app
        # router.add_route('*', '/{notes}/{{instance_id}}'.format(notes=self.notes), self.instance_endpoint.dispatch)

    @parse_request
    async def get_activities(self, show_all):
        from koala.cogs.base import core
        return core.activity_list(show_all=show_all)

    @parse_request
    async def get_activities(self, show_all):
        from koala.cogs.base import core
        return core.activity_list(show_all=show_all)

    # async def get(self) -> Response:
    #     data = []
    #
    #     notes = session.query(Note).all()
    #     for instance in self.resource.collection.values():
    #         data.append(self.resource.render(instance))
    #     data = self.resource.encode(data)
    #     return Response(status=200, body=self.resource.encode({
    #         'notes': [
    #             {'id': note.id, 'title': note.title, 'description': note.description,
    #              'created_at': note.created_at, 'created_by': note.created_by, 'priority': note.priority}
    #
    #             for note in session.query(Note)
    #
    #         ]
    #     }), content_type='application/json')
    #
    # async def post(self, request):
    #     data = await request.json()
    #     note = Note(title=data['title'], description=data['description'], created_at=data['created_at'],
    #                 created_by=data['created_by'], priority=data['priority'])
    #     session.add(note)
    #     session.commit()
    #
    #     return Response(status=201, body=self.resource.encode({
    #         'notes': [
    #             {'id': note.id, 'title': note.title, 'description': note.description,
    #              'created_at': note.created_at, 'created_by': note.created_by, 'priority': note.priority}
    #
    #             for note in session.query(Note)
    #
    #         ]
    #     }), content_type='application/json')


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.

    :param app: the base aiohttp application
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = BaseEndpoint(bot)
    endpoint.register(sub_app)
    bot.__getattribute__("koala_web_app").add_subapp('/{extension}'.format(extension=BASE_ENDPOINT), sub_app)
    logger.info("Base API is ready.")
