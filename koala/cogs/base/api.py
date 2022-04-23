import inspect
import json
from collections import OrderedDict

from aiohttp import web
from aiohttp.http_exceptions import HttpBadRequest
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp.web import Request, Response, Application

from koala.rest.api import RestEndpoint

ACTIVITY_ENDPOINT = 'activity'

class BaseEndpoint(RestEndpoint):
    def __init__(self):
        super().__init__()

    def register(self):
        app = web.Application()
        app.add_routes([web.get('/{activity}'.format(activity=ACTIVITY_ENDPOINT), self.get_activities)])
        return app
        # router.add_route('*', '/{notes}/{{instance_id}}'.format(notes=self.notes), self.instance_endpoint.dispatch)

    async def get_activities(self, request) -> Response:
        from koala.cogs.base import core
        print(core.activity_list(show_all=True))
        return Response(status=200, content_type='application/json')
