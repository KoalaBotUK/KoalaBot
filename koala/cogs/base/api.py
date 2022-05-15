# Futures
# Built-in/Generic Imports
# Libs
from http.client import CREATED, OK
from aiohttp import web
import discord
from discord.ext.commands import Bot

# Own modules
from . import core
from .log import logger
from koala.rest.api import parse_request, build_response
from koala.utils import convert_iso_datetime

# Constants
BASE_ENDPOINT = 'base'
ACTIVITY_ENDPOINT = 'activity'
SET_ACTIVITY_ENDPOINT = 'setActivity'
SCHEDULE_ACTIVITY_ENDPOINT = 'scheduleActivity'

PING_ENDPOINT = 'ping'
SUPPORT_ENDPOINT = 'support'
GET_VERSION_ENDPOINT = 'getVersion'
PURGE_ENDPOINT = 'purge'
LOAD_COG_ENDPOINT = 'loadCog'
UNLOAD_COG_ENDPOINT = 'unloadCog'
ENABLE_EXTENSION_ENDPOINT = 'enableExtension'
DISABLE_EXTENSION_ENDPOINT = 'disableExtension'
LIST_ENABLED_EXTENSIONS_ENDPOINT = 'listEnabledExtensions'

# Variables

class BaseEndpoint:
    """
    The API endpoints for BaseCog
    """
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for the given application
        todo: review aiohttp 'views' and see if they are a better idea
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([web.get('/{endpoint}'.format(endpoint=ACTIVITY_ENDPOINT), self.get_activities),
                        web.put('/{endpoint}'.format(endpoint=SET_ACTIVITY_ENDPOINT), self.put_set_activity),
                        web.post('/{endpoint}'.format(endpoint=SCHEDULE_ACTIVITY_ENDPOINT), self.post_schedule_activity),
                        web.get('/{endpoint}'.format(endpoint=PING_ENDPOINT), self.get_ping),
                        web.get('/{endpoint}'.format(endpoint=SUPPORT_ENDPOINT), self.get_support_link),
                        web.get('/{endpoint}'.format(endpint=GET_VERSION_ENDPOINT), self.get_version),
                        web.delete('/{endpoint}'.format(endpoint=PURGE_ENDPOINT), self.delete_messages),
                        web.get('/{endpoint}'.format(endpoint=LOAD_COG_ENDPOINT), self.get_cog),
                        web.delete('/{endpoint}'.format(endpoint=UNLOAD_COG_ENDPOINT), self.delete_cog)])
        return app

    @parse_request
    async def get_activities(self, show_all: bool):
        """
        Get all the scheduled activities
        :param show_all: If you wish to see a time restricted version or not
        :return: The list of ScheduledActivities
        """
        return core.activity_list(show_all=show_all)

    @parse_request(raw_response=True)
    async def put_set_activity(self, activity_type, name, url):
        """
        Put a given activity as the discord bot's activity
        :param activity_type: activity type (playing, watching, streaming, ...)
        :param name: The content of the activity
        :param url: The url to use (for streaming)
        :return:
        """
        try:
            activity_type = getActivityType(activity_type)
            await core.activity_set(activity_type, name, url, self._bot)
        except BaseException as e:
            error = 'Error setting activity: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        return build_response(CREATED, {'message': 'Activity set'})

    @parse_request(raw_response=True)
    async def post_schedule_activity(self, activity_type, message, url, start_time, end_time):
        """
        Post a given activity as a scheduled activity
        :param activity_type: activity type (playing, watching, streaming, ...)
        :param message: message to be used in sidebar
        :param url: optional url to use (for streaming)
        :param start_time: start time of activity to be used
        :param end_time: end time of activity to be used
        :return:
        """
        try:
            start_time = convert_iso_datetime(start_time)
            end_time = convert_iso_datetime(end_time)
            activity_type = getActivityType(activity_type)
            core.activity_schedule(activity_type, message, url, start_time, end_time)
        except BaseException as e:
            error = 'Error scheduling activity: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))

        return build_response(CREATED, {'message': 'Activity scheduled'})

    @parse_request
    async def get_ping(self):
        """
        Get the latency of the bot
        :return: The ping
        """
        return core.ping(self._bot)

    @parse_request
    async def get_support_link():
        """
        Get the support link of KoalaBot
        :return: The support link
        """
        return core.support_link()

    @parse_request
    async def get_version(self):
        """
        Get the version of KoalaBot
        :return: The version
        """
        return core.get_version(self._bot)

    @parse_request
    async def delete_messages(self, channel_id, amount):
        """
        Delete messages from a given channel
        :param channel_id: channel to delete messages
        :param amount: number of messages to delete
        :return:
        """
        try:
            core.purge(self._bot, channel_id, amount)
        except BaseException as e:
            error = 'Error deleting messages: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))

        return build_response(OK, {'message': 'Message(s) deleted'})

    @parse_request
    async def get_cog(self, extension, package):
        """
        Loads a cog from the cogs folder
        :param extension: name of the cog
        :param package: package of the cogs
        :return:
        """
        try:
            core.load_cog(self._bot, extension, package)
        except BaseException as e:
            error = 'Error loading cog: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        return build_response(OK, {'message': 'Cog loaded'})

    @parse_request
    async def delete_cog(self, extension, package):
        """
        Unloads a cog from the cogs folder
        :param extension: name of the cog
        :param package: package of the cogs
        :return:
        """
        try:
            core.unload_cog(self._bot, extension, package)
        except BaseException as e:
            error = 'Error unloading cog: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        return build_response(OK, {'message': 'Cog unloaded'})



def getActivityType(activity_type):
    return discord.ActivityType[activity_type]


def handleActivityError(error):
    if type(error) == KeyError:
        return 'Invalid activity type'
    elif type(error) == discord.ext.commands.errors.BadArgument:
        return 'Bad start / end time' 
    return 'Unknown error'


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = BaseEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{extension}'.format(extension=BASE_ENDPOINT), sub_app)
    logger.info("Base API is ready.")
