# Futures

# Built-in/Generic Imports
import re

# Libs
import discord
from sqlalchemy import select, delete, and_, null
from sqlalchemy.orm import joinedload, Session
from twitchAPI.object import Stream

# Own modules
from koala.db import session_manager
from .env import TWITCH_KEY, TWITCH_SECRET
from .log import logger
from .models import TwitchAlerts, TeamInTwitchAlert, UserInTwitchTeam, UserInTwitchAlert
from .twitch_handler import TwitchAPIHandler
from .utils import DEFAULT_MESSAGE, TWITCH_USERNAME_REGEX, create_live_embed


# Constants

# Variables


def delete_invalid_accounts():
    """
    Removes invalid teams & users (where the names are not valid according to the twitch Regex)
    :return:
    """
    with session_manager() as session:
        usernames = session.execute(select(UserInTwitchAlert.twitch_username))
        teams = session.execute(select(TeamInTwitchAlert.twitch_team_name))
        users_in_teams = session.execute(select(UserInTwitchTeam.twitch_username))

        invalid_usernames = [user for user in usernames
                             if not re.search(TWITCH_USERNAME_REGEX, user.twitch_username)]
        invalid_teams = [team.twitch_team_name for team in teams
                         if not re.search(TWITCH_USERNAME_REGEX, team.twitch_team_name)]
        invalid_users_in_teams = [user.twitch_username for user in users_in_teams
                                  if not re.search(TWITCH_USERNAME_REGEX, user.twitch_username)]

        if invalid_usernames:
            logger.warning(f'Deleting Invalid Users')
        if invalid_teams:
            logger.warning(f'Deleting Invalid Teams')
        if invalid_users_in_teams:
            logger.warning(f'Deleting Invalid Users in Teams')

        delete_invalid_usernames = delete(UserInTwitchAlert)\
            .where(UserInTwitchAlert.twitch_username.in_(invalid_usernames))
        delete_invalid_teams = delete(TeamInTwitchAlert)\
            .where(TeamInTwitchAlert.twitch_team_name.in_(invalid_teams))
        # This should be nothing
        delete_invalid_users_in_teams = delete(TeamInTwitchAlert)\
            .where(TeamInTwitchAlert.twitch_team_name.in_(invalid_teams))

        session.execute(delete_invalid_usernames)
        session.execute(delete_invalid_teams)
        session.execute(delete_invalid_users_in_teams)
        session.commit()


class TwitchAlertDBManager:
    """
    A class for interacting with the Koala twitch database
    """
    twitch_handler: TwitchAPIHandler

    def __init__(self, bot_client: discord.client):
        """
        Initialises local variables
        :param bot_client:
        """
        delete_invalid_accounts()
        self.bot = bot_client


