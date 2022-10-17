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
EMAIL_ENDPOINT = 'email'
ENABLE_VERIFICATION_ENDPOINT = 'enable-verification'
DISABLE_VERIFICATION_ENDPOINT = 'disable-verification'

# Variables

class VerifyEndpoint:
    """
    THe API endpoints for Verification
    """
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for Verify Cog
        todo: review aiohttp 'views' and see if they are a better idea
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([web.get('/{endpoint}'.format(endpoint=EMAIL_ENDPOINT), self.put_email),
                        web.get('/{endpoint}'.format(endpoint=ENABLE_VERIFICATION_ENDPOINT), self.put_enable_verification),
                        web.get('/{endpoint}'.format(endpoint=DISABLE_VERIFICATION_ENDPOINT), self.put_disable_verification)])
        return app

    @parse_request(raw_response=True)
    async def put_email(self, email, token):
        """
        Sends an email through gmails smtp server from the email stored in the environment variables
        :param email: target to send an email to
        :param token: the token the recipient will need to verify with
        :return:
        """
        try:
            await core.send_email(email, token)
        except BaseException as e:
            error = 'Error sending email request: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason='{}'.format(error))
        return build_response(CREATED, {'message': 'Email sent'})

    @parse_request(raw_response=True)
    async def put_enable_verification(self, guild_id, guild_roles, email_suffix, role):
        """
        Set up a role and email pair for KoalaBot to verify users with
        :param guild_id: guild id of current guild
        :param guild_roles: all enabled roles in the current guild
        :param email_suffix: end of the email (e.g. "example.com")
        :param role: the role to give users with that email verified (e.g. @students)
        :return:
        """
        try:
            await core.enable_verification(
                guild_id=guild_id,
                guild_roles=guild_roles,
                suffix=email_suffix,
                role=role
            )
        except BaseException as e:
            error = 'Error enabling verification: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason='{}'.format(error))
        return build_response(CREATED, {'message': 'Verification enabled'})

    @parse_request(raw_response=True)
    async def put_disable_verification(self, guild_id, email_suffix, role):
        """
        Disable an existing verification listener
        :param guild_id: guild id of current guild
        :param email_suffix: end of the email (e.g. "example.com")
        :param role: the role paired with the email (e.g. @students)
        :return:
        """
        try:
            await core.disable_verification(
                guild_id=guild_id,
                suffix=email_suffix,
                role=role
            )
        except BaseException as e:
            error = 'Error disabling verification: {}'.format(handleActivityError(e))
            logger.error(error)
            raise web.HTTPUnprocessableEntity(reason='{}'.format(error))
        return build_response(CREATED, {'message': 'Verification disabled'})

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
