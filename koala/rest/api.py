import dataclasses
import datetime
import inspect
import json
from collections import OrderedDict
from functools import wraps

from aiohttp.http_exceptions import HttpBadRequest
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp.web import Request, Response
from aiohttp.web_urldispatcher import UrlDispatcher

from koala.models import BaseModel

DEFAULT_METHODS = ('GET', 'POST', 'PUT', 'DELETE')


class RestEndpoint:

    def __init__(self):
        self.methods = {}

        for method_name in DEFAULT_METHODS:
            method = getattr(self, method_name.lower(), None)
            if method:
                self.register_method(method_name, method)

    def register_method(self, method_name, method):
        self.methods[method_name.upper()] = method

    async def dispatch(self, request: Request):
        # if request.method.upper() == "GET":
        #     potentials =
        # elif request.method.upper() == "POST":
        #
        # else:
        #     raise HTTPMethodNotAllowed('', DEFAULT_METHODS)
        method = self.methods.get(request.method.upper())

        wanted_args = list(inspect.signature(method).parameters.keys())
        available_args = request.match_info.copy()
        available_args.update({'request': request})

        unsatisfied_args = set(wanted_args) - set(available_args.keys())
        if unsatisfied_args:
            # Expected match info that doesn't exist
            raise HttpBadRequest('')

        return await method(**{arg_name: available_args[arg_name] for arg_name in wanted_args})


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.as_dict()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)


def parse_request(*args, **kwargs):

    func = None
    if len(args) == 1 and callable(args[0]):
        func = args[0]

    if func:
        raw_response = False  # default values

    if not func:
        raw_response = kwargs.get('raw_response')

    def parsed_request(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]
            request = args[1]
            wanted_args = list(inspect.signature(func).parameters.keys())
            wanted_args.remove("self")
            available_args = await request.json()
            available_args.update({'request': request})

            unsatisfied_args = set(wanted_args) - set(available_args.keys())
            if unsatisfied_args:
                # Expected match info that doesn't exist
                raise HttpBadRequest('')

            result = await func(self, **{arg_name: available_args[arg_name] for arg_name in wanted_args})
            if raw_response:
                return result
            else:
                return Response(status=200,
                                body=json.dumps(result, cls=EnhancedJSONEncoder),
                                content_type='application/json')

        return wrapper
    return parsed_request(func) if func else parsed_request
