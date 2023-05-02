# Futures
# Built-in/Generic Imports
import dataclasses
import datetime
import inspect
import json
# Libs
from functools import wraps
from http.client import OK, BAD_REQUEST

import aiohttp.web
from aiohttp.abc import Request
from aiohttp.typedefs import Handler

from koala.errors import KoalaException
from koala.log import logger
# Own modules
from koala.models import BaseModel
from koala.rest.dto import ApiError, StringApiResponse


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


def build_response(status_code, data):
    """
    Build a response object
    :param status_code:
    :param data:
    :return:
    """
    if data is not None:
        body = json.dumps(data, cls=EnhancedJSONEncoder)
    else:
        body = None

    return aiohttp.web.Response(status=status_code,
                                body=body,
                                content_type='application/json')


def parse_request(*args, **kwargs) -> Handler:
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
            request: Request = args[1]

            wanted_args: dict[str, inspect.Parameter] = dict(inspect.signature(func).parameters)
            wanted_args.pop("self")

            required_args: dict[str, inspect.Parameter] = {a: wanted_args.get(a) for a in wanted_args.keys() if
                                                           wanted_args.get(a).default == inspect.Parameter.empty}

            available_args = {}

            if (request.method in request.POST_METHODS) and request.can_read_body:
                body = await request.json()
                for arg in wanted_args.keys():
                    if arg in body:
                        available_args[arg] = body[arg]
            else:
                for arg in wanted_args.keys():
                    if arg in request.query:
                        available_args[arg] = request.query[arg]

            unsatisfied_args = set(required_args.keys()) - set(available_args.keys())
            if unsatisfied_args:
                # Expected match info that doesn't exist
                return build_response(BAD_REQUEST, ApiError("BAD_REQUEST",
                                                            "Unsatisfied Arguments: %s" % unsatisfied_args))

            try:
                result = await func(self, **{arg_name: available_args[arg_name] for arg_name in available_args.keys()})
                if isinstance(result, str):
                    result = StringApiResponse(result)

            except Exception as e:
                logger.error("API Failed", exc_info=e)
                return build_response(BAD_REQUEST, ApiError(type(e).__name__, str(e)))
            if raw_response:
                return result
            else:
                return build_response(OK, result)

        return wrapper

    return parsed_request(func) if func else parsed_request
