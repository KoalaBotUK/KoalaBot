# Futures
# Built-in/Generic Imports
# Libs
from http.client import CREATED, OK
from typing import Optional

import discord
from aiohttp import web
from discord.ext.commands import Bot

from koala.rest.api import parse_request, build_response
# Own modules
from . import core
from .log import logger

# Constants
VOTING_ENDPOINT = 'voting'
CONFIG_ENDPOINT = 'config'
RESULTS_ENDOPINT = 'results'

# Variables

class VotingEndpoint:
    """
    The API endpoints for Voting
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
        app.add_routes([web.post('/{endpoint}'.format(endpoint=CONFIG_ENDPOINT), self.post_new_vote),
                        web.get('/{endpoint}'.format(endpoint=CONFIG_ENDPOINT), self.get_current_votes),
                        web.post('/{endpoint}'.format(endpoint=RESULTS_ENDOPINT), self.post_close_results),
                        web.get('/{endpoint}'.format(endpoint=RESULTS_ENDOPINT), self.get_results)])
        return app
    

# how to do vote_manager
    @parse_request
    async def post_new_vote(self, title, author_id, guild_id, options: list,
                            roles: Optional[list], chair_id: Optional[int], end_time: Optional[str]):
        """
        Create a new vote.
        :param title: The name of the vote
        :param author_id: The author id of the vote
        :param guild_id: The guild id of the vote 
        :param options: The options for the votes
        :param roles: The target roles for the votes
        :param chair_id: The chair id of the vote
        :param end_time: The end time of the vote
        :return:
        """
        try:
            await core.start_vote(self, self.vote_manager, title, author_id, guild_id)

            for item in options:
                core.add_option(self.vote_manager, author_id, item)

            if roles:
                for item in roles:
                    core.set_roles(self, self.vote_manager, author_id, guild_id, item, "add")

            if chair_id:
                core.set_chair(self, self.vote_manager, author_id, chair_id)

            if end_time:
                core.set_end_time(self.vote_manager, author_id, end_time)

            await core.send_vote(self, self.vote_manager, author_id, guild_id)

        except Exception as e:
            logger.error(e)
            raise web.HTTPUnprocessableEntity()

        return build_response(CREATED, {'message': f'Vote {title} created'})
    

    @parse_request
    def get_current_votes(self, author_id, guild_id):
        """
        Gets list of open votes.
        :param author_id: The author id of the vote
        :param guild: The guild id of the vote
        :return:
        """
        try:
            embed = core.current_votes(author_id, guild_id)
        except Exception as e:
            logger.error(e)
            raise web.HTTPUnprocessableEntity()
        
        return build_response(OK, embed)
    

    @parse_request
    async def post_close_results(self, author_id, title):
        """
        Gets results and closes the vote.
        :param author_id: The author id of the vote
        :param title: The title of the vote
        :return:
        """
        try:
            embed = await core.close(self, self.vote_manager, author_id, title)
        except Exception as e:
            logger.error(e)
            raise web.HTTPUnprocessableEntity()
        
        return build_response(OK, embed)
    

    @parse_request
    async def get_results(self, author_id, title):
        """
        Gets results, but does not close the vote.
        :param author_id: The author id of the vote
        :param title: The title of the vote
        :return:
        """
        try:
            embed = core.results(self, self.vote_manager, author_id, title)
        except Exception as e:
            logger.error(e)
            raise web.HTTPUnprocessableEntity()
        
        return build_response(OK, embed)
    

def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = VotingEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{extension}'.format(extension=VOTING_ENDPOINT), sub_app)
    logger.info("Voting API is ready.")
