# Futures
# Built-in/Generic Imports
import dataclasses
import datetime
import inspect
import json

# Libs
from functools import wraps
import aiohttp.web
from aiohttp.web import Response

# Own modules
from koala.models import BaseModel

# Constants

# Variables


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder for datatypes used for this project
    """
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.as_dict()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)


def parse_request(*args, **kwargs):
    """
    A wrapper for API endpoints that provide the required args
    if raw_response = true, then the default response type is not applied

    Example usage:
      class Api:
        ...
        @parse_request
        async def post(self, request, field, field2):
          return "done"
        ...
        @parse_request(raw_response=True)
        async def get(self, request, field, field2):
          return Response(status=200,
                                text="done",
                                content_type='application/json')


    todo: add type parsing/conversion based on wanted_arg types
    :param args:
    :param kwargs:
    :return:
    """

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
                raise aiohttp.web.HTTPBadRequest(reason="Unsatisfied Arguments: %s" % unsatisfied_args)

            result = await func(self, **{arg_name: available_args[arg_name] for arg_name in wanted_args})
            if raw_response:
                return result
            else:
                return Response(status=200,
                                body=json.dumps(result, cls=EnhancedJSONEncoder),
                                content_type='application/json')

        return wrapper
    return parsed_request(func) if func else parsed_request
