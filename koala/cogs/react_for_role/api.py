# Futures
# Built-in/Generic Imports
# Libs
from typing import List

import discord
from aiohttp import web
from discord.ext.commands import Bot

import koalabot
from koala.rest.api import parse_request
# Own modules
from . import core
from .dto import ReactRole
from .log import logger
from ... import colours

# Constants
RFR_ENDPOINT = 'react-for-role'

MESSAGE = 'message'
REQUIRED_ROLES = 'required-roles'


class RfrEndpoint:
    _bot: koalabot.KoalaBot
    """
    The API endpoints for BaseCog
    """

    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for the given application
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([web.post('/{}'.format(MESSAGE), self.post_message),
                        web.get('/{}'.format(MESSAGE), self.get_message),
                        web.put('/{}'.format(MESSAGE), self.put_message),
                        web.patch('/{}'.format(MESSAGE), self.patch_message),
                        web.delete('/{}'.format(MESSAGE), self.delete_message),
                        web.put('/{}'.format(REQUIRED_ROLES), self.put_required_roles),
                        web.get('/{}'.format(REQUIRED_ROLES), self.get_required_roles)])
        return app

    @parse_request
    async def post_message(self,
                           guild_id: int,
                           channel_id: int,
                           title: str,
                           description: str = "",
                           colour: str = colours.KOALA_GREEN.__str__(),
                           thumbnail: str = None,
                           inline: bool = None,
                           roles: List[dict] = None
                           ):
        """
        Create a React For Role message

        :param guild_id: Guild ID of RFR message
        :param channel_id: Channel ID of RFR message
        :param title: Title of RFR message
        :param description: Description of RFR message
        :param colour: Hex colour code of RFR message
        :param thumbnail: thumbnail URL
        :param inline: fields should be inline
        :param roles: roles for RFR message
        :return:
        """
        guild = self._bot.get_guild(guild_id)
        if roles is not None:
            roles = [ReactRole(r["emoji"], r["role_id"]).to_tuple(guild) for r in roles]

        return await core.create_rfr_message(bot=self._bot,
                                             guild_id=guild_id,
                                             channel_id=channel_id,
                                             title=title,
                                             description=description,
                                             colour=discord.Colour.from_str(colour),
                                             thumbnail=thumbnail,
                                             inline=inline,
                                             roles=roles)

    @parse_request
    async def get_message(self,
                          message_id: int,
                          guild_id: int,
                          channel_id: int
                          ):
        """
        Get a React For Role message

        :param message_id: Message ID of RFR message
        :param guild_id: Guild ID of RFR message
        :param channel_id: Channel ID of RFR message
        :return:
        """
        return await core.get_rfr_message_dto(self._bot, int(message_id), int(guild_id), int(channel_id))

    @parse_request
    async def put_message(self,
                          message_id: int,
                          guild_id: int,
                          channel_id: int,
                          title: str,
                          description: str,
                          colour: str,
                          thumbnail: str,
                          inline: bool,
                          roles: List[dict]
                          ):
        """
        Edit a React For Role message

        :param message_id: Message ID of RFR message
        :param guild_id: Guild ID of RFR message
        :param channel_id: Channel ID of RFR message
        :param title: Title of RFR message
        :param description: Description of RFR message
        :param colour: Hex colour code of RFR message
        :param thumbnail: thumbnail URL
        :param inline: fields should be inline
        :param roles: roles for RFR message
        :return:
        """
        guild = self._bot.get_guild(guild_id)
        if roles is not None:
            roles = [ReactRole(r["emoji"], r["role_id"]).to_tuple(guild) for r in roles]
        return await core.update_rfr_message(bot=self._bot,
                                             message_id=message_id,
                                             guild_id=guild_id,
                                             channel_id=channel_id,
                                             title=title,
                                             description=description,
                                             colour=discord.Colour.from_str(colour),
                                             thumbnail=thumbnail,
                                             inline=inline,
                                             roles=roles)

    @parse_request
    async def patch_message(self,
                            message_id: int,
                            guild_id: int,
                            channel_id: int,
                            title: str = None,
                            description: str = None,
                            colour: str = None,
                            thumbnail: str = None,
                            inline: bool = None,
                            roles: List[dict] = None
                            ):
        """
        Edit a React For Role message

        :param message_id: Message ID of RFR message
        :param guild_id: Guild ID of RFR message
        :param channel_id: Channel ID of RFR message
        :param title: Title of RFR message
        :param description: Description of RFR message
        :param colour: Hex colour code of RFR message
        :param thumbnail: thumbnail URL
        :param inline: fields should be inline
        :param roles: roles for RFR message
        :return:
        """
        guild = self._bot.get_guild(guild_id)
        if roles is not None:
            roles = [ReactRole(r["emoji"], r["role_id"]).to_tuple(guild) for r in roles]

        if colour is not None:
            colour = discord.Colour.from_str(colour)

        return await core.update_rfr_message(bot=self._bot,
                                             message_id=message_id,
                                             guild_id=guild_id,
                                             channel_id=channel_id,
                                             title=title,
                                             description=description,
                                             colour=colour,
                                             thumbnail=thumbnail,
                                             inline=inline,
                                             roles=roles)

    @parse_request
    async def delete_message(self,
                             message_id: int,
                             guild_id: int,
                             channel_id: int
                             ):
        """
        Delete a React For Role message

        :param message_id: Message ID of RFR message
        :param guild_id: Guild ID of RFR message
        :param channel_id: Channel ID of RFR message
        :return:
        """
        await core.delete_rfr_message(self._bot, int(message_id), int(guild_id), int(channel_id))
        return {"status": "DELETED",  "message_id": message_id}

    @parse_request
    async def put_required_roles(self,
                                 guild_id: int,
                                 role_ids: List[int] = None
                                 ):
        """
        Set or edit RFR required roles for a guild

        :param guild_id: Guild ID of RFR message
        :param role_ids: List of required role IDs
        :return:
        """
        core.edit_guild_rfr_required_roles(self._bot, guild_id, role_ids)
        return core.rfr_list_guild_required_roles(self._bot.get_guild(int(guild_id)))

    @parse_request
    async def get_required_roles(self, guild_id: int):
        """
        Get RFR required roles for a guild

        :param guild_id: Guild ID of RFR message
        :return:
        """
        return core.rfr_list_guild_required_roles(self._bot.get_guild(int(guild_id)))


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = RfrEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{}'.format(RFR_ENDPOINT), sub_app)
    logger.info("RFR API is ready.")
