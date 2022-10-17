# Futures
# Built-in/Generic Imports
# Libs
from http.client import CREATED, OK, BAD_REQUEST
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
ACTIVITY_ENDPOINT = 'activity' # PUT
SCHEDULED_ACTIVITY_ENDPOINT = 'scheduled-activity' # POST

PING_ENDPOINT = 'ping'
SUPPORT_ENDPOINT = 'support'
GET_VERSION_ENDPOINT = 'version'
LOAD_COG_ENDPOINT = 'load-cog'
UNLOAD_COG_ENDPOINT = 'unload-cog'
ENABLE_EXTENSION_ENDPOINT = 'enable-extension'
DISABLE_EXTENSION_ENDPOINT = 'disable-extension'
EXTENSIONS_ENDPOINT = 'extensions'

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
        app.add_routes([web.get('/{endpoint}'.format(endpoint=SCHEDULED_ACTIVITY_ENDPOINT), self.get_activities),
                        web.put('/{endpoint}'.format(endpoint=ACTIVITY_ENDPOINT), self.put_set_activity),
                        web.put('/{endpoint}'.format(endpoint=SCHEDULED_ACTIVITY_ENDPOINT), self.put_schedule_activity),
                        web.get('/{endpoint}'.format(endpoint=PING_ENDPOINT), self.get_ping),
                        web.get('/{endpoint}'.format(endpoint=SUPPORT_ENDPOINT), self.get_support_link),
                        web.get('/{endpoint}'.format(endpoint=GET_VERSION_ENDPOINT), self.get_version),
                        web.post('/{endpoint}'.format(endpoint=LOAD_COG_ENDPOINT), self.post_load_cog),
                        web.post('/{endpoint}'.format(endpoint=UNLOAD_COG_ENDPOINT), self.post_unload_cog),
                        web.post('/{endpoint}'.format(endpoint=ENABLE_EXTENSION_ENDPOINT), self.post_enable_extension),
                        web.post('/{endpoint}'.format(endpoint=DISABLE_EXTENSION_ENDPOINT), self.post_disable_extension),
                        web.get('/{endpoint}'.format(endpoint=EXTENSIONS_ENDPOINT), self.get_extensions)])
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
    async def put_schedule_activity(self, activity_type, message, url, start_time, end_time):
        """
        Put a given activity as a scheduled activity
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
        return await core.ping(self._bot)

    @parse_request
    async def get_support_link(self):
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
        return core.get_version()

    @parse_request
    async def post_load_cog(self, extension, package):
        """
        Loads a cog from the cogs folder
        :param extension: name of the cog
        :param package: package of the cogs
        :return:
        """
        try:
            await core.load_cog(self._bot, extension, package)
        except BaseException as e:
            error = 'Error loading cog: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        return {'message': 'Cog loaded'}

    @parse_request
    async def post_unload_cog(self, extension, package):
        """
        Unloads a cog from the cogs folder
        :param extension: name of the cog
        :param package: package of the cogs
        :return:
        """
        try:
            await core.unload_cog(self._bot, extension, package)
        except BaseException as e:
            error = 'Error unloading cog: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        # if resp == "Sorry, you can't unload the base cog":
        #     return build_response(BAD_REQUEST, {'message': "Sorry, you can't unload the base cog"})
        # else:
        return {'message': 'Cog unloaded'}

    @parse_request
    async def post_enable_extension(self, guild_id, koala_ext):
        """
        Enables a koala extension
        :param guild_id: id for the Discord guild
        :param koala_ext: name of the extension
        :return:
        """
        try:
            await core.enable_extension(self._bot, guild_id, koala_ext)
        except BaseException as e:
            print(type(e))
            error = 'Error enabling extension: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        return {'message': 'Extension enabled'}

    @parse_request
    async def post_disable_extension(self, guild_id, koala_ext):
        """
        Disables a koala extension onto a server
        :param guild_id: id for the Discord guild
        :param koala_extension: name of the extension
        :return:
        """
        try:
            await core.disable_extension(self._bot, guild_id, koala_ext)
        except BaseException as e:
            print(type(e))
            error = 'Error disabling extension: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason="{}".format(error))
        
        return {'message': 'Extension disabled'}

    @parse_request
    async def get_extensions(self, guild_id):
        """
        Gets enabled koala extensions of a guild
        :param guild_id: id of the Discord guild
        :return:
        """
        return await core.get_available_extensions(guild_id)



def getActivityType(activity_type):
    return discord.ActivityType[activity_type]

# Extract into new file?
def handleActivityError(error):
    if type(error) == KeyError:
        return 'Invalid activity type'
    elif type(error) == discord.ext.commands.errors.BadArgument:
        return 'Bad start / end time'
    elif type(error) == discord.ext.commands.errors.ExtensionNotFound:
        return 'Invalid extension'
    elif type(error) == discord.ext.commands.errors.ExtensionNotLoaded:
        return 'Extension not loaded'
    elif type(error) == discord.ext.commands.errors.ExtensionAlreadyLoaded:
        return 'Already loaded'
    elif type(error) == NotImplementedError and str(error).endswith("not an enabled extension"):
        return 'Extension not enabled'
    elif type(error) == NotImplementedError and str(error).endswith("not a valid extension"):
        return 'Invalid extension'
    elif type(error) == discord.ext.commands.errors.ExtensionFailed:
        return 'Failed to load'
    elif type(error) == discord.ext.commands.errors.ExtensionError and str(error).endswith("base cog"):
        return "Sorry, you can't unload the base cog"
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
