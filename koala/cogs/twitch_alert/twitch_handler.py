# Futures
from typing import List

from twitchAPI.object import Stream, TwitchUser, Game, ChannelTeam

# Built-in/Generic Imports

# Own modules
from .utils import split_to_100s
from .log import logger

# Libs
from twitchAPI.twitch import Twitch
from twitchAPI.types import TwitchAPIException

# Constants


# Variables

class TwitchAPIHandler:
    """
    A wrapper to interact with the twitch API
    """
    twitch: Twitch

    async def setup(self, client_id: str, client_secret: str):
        self.twitch = await Twitch(client_id, client_secret)

    async def get_streams_data(self, usernames) -> List[Stream]:
        """
        Gets all stream information from a list of given usernames
        :param usernames: The list of usernames
        :return: The JSON data of the request
        """
        result: List[Stream] = []
        batches = split_to_100s(usernames)
        for batch in batches:
            batch_result: List[Stream] = []
            try:
                async for stream in self.twitch.get_streams(user_login=batch):
                    batch_result.append(stream)
            except TwitchAPIException:
                logger.error(f"Streams data not received for batch, invalid request")
                for user in batch:
                    try:
                        async for stream in self.twitch.get_streams(user_login=user):
                            batch_result.append(stream)
                    except TwitchAPIException:
                        logger.error("User data cannot be found, invalid request")

            result.extend(batch_result)

        return result

    async def get_user_data(self, usernames=None, ids=None) -> List[TwitchUser]:
        """
        Gets the user information of a given user

        :param usernames: The display twitch usernames of the users
        :param ids: The unique twitch ids of the users
        :return: The JSON information of the user's data
        """
        result = []

        if usernames:
            user_list = split_to_100s(usernames)
            for u_batch in user_list:
                async for user in self.twitch.get_users(logins=u_batch):
                    result.append(user)

        if ids:
            id_list = split_to_100s(ids)
            for id_batch in id_list:
                async for user in self.twitch.get_users(logins=id_batch):
                    result.append(user)

        return result

    async def get_game_data(self, game_id) -> Game:
        """
        Gets the game information of a given game
        :param game_id: The twitch game ID of a game
        :return: The JSON information of the game's data
        """
        if game_id != "":
            async for game in self.twitch.get_games(game_ids=game_id):
                return game

    async def get_team_users(self, team_id):
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        return (await self.get_team_data(team_id)).users

    async def get_team_data(self, team_id) -> ChannelTeam:
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        return await self.twitch.get_teams(name=team_id)
