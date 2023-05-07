# Futures
# Built-in/Generic Imports
# Libs
from http.client import CREATED

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
    

    @parse_request
    async def post_new_vote(self):
        """
        Create a new vote.
        :param : 
        :return: The list of ScheduledActivities
        """
        pass
    

    @parse_request
    async def get_current_votes(self):
        """
        Gets list of open votes.
        """
        pass
    

    @parse_request
    async def post_close_results(self):
        """
        Gets results and closes the vote.
        """
        pass


    @parse_request
    async def get_results(self):
        """
        Gets results, but does not close the vote.
        """
        pass
    

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
