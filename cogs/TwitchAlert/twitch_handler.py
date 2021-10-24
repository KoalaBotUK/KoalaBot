# Futures

# Built-in/Generic Imports

# Own modules
from .utils import split_to_100s
from log import logging

# Libs
from twitchAPI.twitch import Twitch
from twitchAPI.types import TwitchAPIException

# Constants


# Variables

class TwitchAPIHandler:
    """
    A wrapper to interact with the twitch API
    """

    def __init__(self, client_id: str, client_secret: str):
        self.twitch = Twitch(client_id, client_secret)

    def get_streams_data(self, usernames):
        """
        Gets all stream information from a list of given usernames
        :param usernames: The list of usernames
        :return: The JSON data of the request
        """
        result = []
        batches = split_to_100s(usernames)
        for batch in batches:
            batch_result = []
            try:
                batch_result.extend(self.twitch.get_streams(user_login=batch).get("data"))
            except TwitchAPIException:
                logging.error(f"TwitchAlert: Streams data not received for batch: {batch}")
                for user in batch:
                    try:
                        batch_result.extend(self.twitch.get_streams(user_login=user).get("data"))
                    except TwitchAPIException:
                        logging.error(f"TwitchAlert: User data cannot be found | {user} ")
            result.extend(batch_result)

        return result

    def get_user_data(self, usernames=None, ids=None):
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
                result += self.twitch.get_users(logins=u_batch).get("data")

        if ids:
            id_list = split_to_100s(ids)
            for id_batch in id_list:
                result += self.twitch.get_users(logins=id_batch).get("data")

        return result

    def get_game_data(self, game_id):
        """
        Gets the game information of a given game
        :param game_id: The twitch game ID of a game
        :return: The JSON information of the game's data
        """
        if game_id != "":
            game_data = self.twitch.get_games(game_ids=game_id)
            return game_data.get("data")[0]
        else:
            return None

    def get_team_users(self, team_id):
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        return (self.get_team_data(team_id)).get("users")

    def get_team_data(self, team_id):
        """
        Gets the users data about a given team
        :param team_id: The team name of the twitch team
        :return: the JSON information of the users
        """
        a = self.twitch.get_teams(name=team_id)
        return a.get("data")[0]
