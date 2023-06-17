# Futures
# Built-in/Generic Imports
# Libs
from typing import List

from aiohttp import web
from discord.ext.commands import Bot

from koala.rest.api import parse_request
# Own modules
from . import core
from .dto import VerifyRole
from .log import logger

# Constants
VERIFY_ENDPOINT = 'verify'
CONFIG_ENDPOINT = 'config'
REVERIFY_ENDPOINT = 'reverify'

# Variables


class VerifyEndpoint:
    """
    The API endpoints for Verify
    """
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for the given application
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([web.get('/{}'.format(CONFIG_ENDPOINT), self.get_verify_config),
                        web.put('/{}'.format(CONFIG_ENDPOINT), self.put_verify_config),
                        web.post('/{}'.format(REVERIFY_ENDPOINT), self.post_reverify)])
        return app

    @parse_request
    async def get_verify_config(self, guild_id: int):
        """
        Get verify config for a given server
        :param guild_id: Guild ID of server
        :return: VerifyConfig
        """
        guild_id = int(guild_id)
        return core.get_verify_config_dto(guild_id)

    @parse_request
    async def put_verify_config(self, guild_id: int, roles: List[dict]):
        """
        Set verify config for a given server
        :param guild_id: Guild ID of server
        :param roles: List of VerifyRole
        :return: VerifyConfig
        """
        guild_id = int(guild_id)
        if roles is not None:
            roles = [VerifyRole(r["email_suffix"], r["role_id"]) for r in roles]

        return await core.set_verify_role(guild_id, roles, self._bot)

    @parse_request
    async def post_reverify(self, guild_id: int, role_id: int):
        """
        Mark a role for re-verification in a server
        :param guild_id: Guild ID of server
        :param role_id: Role ID to be re-verified
        :return: Role ID
        """
        guild_id = int(guild_id)
        role_id = int(role_id)
        await core.re_verify_role(guild_id, role_id, self._bot)
        return {"role_id": role_id}


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = VerifyEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{}'.format(VERIFY_ENDPOINT), sub_app)
    logger.info("Verify API is ready.")
