# Futures

# Built-in/Generic Imports
import re

# Own modules
from koala.db import session_manager

from .twitch_handler import TwitchAPIHandler
from .models import TwitchAlerts, TeamInTwitchAlert, UserInTwitchTeam, UserInTwitchAlert
from .utils import DEFAULT_MESSAGE, TWITCH_USERNAME_REGEX
from .log import logger
from .env import TWITCH_KEY, TWITCH_SECRET

# Libs
import discord
from sqlalchemy import select, delete, and_, null
from sqlalchemy.orm import selectinload


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

    def __init__(self, bot_client: discord.client):
        """
        Initialises local variables
        :param bot_client:
        """
        delete_invalid_accounts()

        self.twitch_handler = TwitchAPIHandler(TWITCH_KEY, TWITCH_SECRET)
        self.bot = bot_client

    def new_ta(self, guild_id, channel_id, default_message=None, replace=False):
        """
        Creates a new Twitch Alert and gives the default message associated with it
        :param guild_id: The discord guild ID where the Twitch Alert is located
        :param channel_id: The discord channel ID of the twitch Alert
        :param default_message: The default message of users in the Twitch Alert
        :param replace: True if the new ta should replace the current if exists
        :return: The new default_message
        """
        # Sets the default message if not provided
        if default_message is None:
            default_message = DEFAULT_MESSAGE
        with session_manager() as session:
            sql_find_ta = select(TwitchAlerts.default_message).where(
                and_(TwitchAlerts.channel_id == channel_id, TwitchAlerts.guild_id == guild_id))
            message: TwitchAlerts = session.execute(sql_find_ta).one_or_none()
            if message and ((not replace) or (default_message == message.default_message)):
                return message.default_message

            # Insert new Twitch Alert to database
            if message:
                message.default_message = default_message
            else:
                session.add(TwitchAlerts(guild_id=guild_id, channel_id=channel_id, default_message=default_message))
            session.commit()
            return default_message

    def get_default_message(self, channel_id):
        """
        Get the set default message for the twitch alert
        :param channel_id: The discord channel ID of the twitch Alert
        :return: The current default_message
        """
        with session_manager() as session:
            result = session.execute(
                select(TwitchAlerts.default_message)
                .filter_by(channel_id=channel_id)
            ).one_or_none()
        if result:
            return result.default_message
        else:
            return DEFAULT_MESSAGE

    def add_user_to_ta(self, channel_id, twitch_username, custom_message, guild_id):
        """
        Add a twitch user to a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_username: The Twitch username of the user to be added
        :param custom_message: The custom Message of the user's live notification.
            None = use default Twitch Alert message
        :param guild_id: The guild ID of the channel
        :return:
        :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
        """
        self.new_ta(guild_id, channel_id)
        with session_manager() as session:
            new_user = UserInTwitchAlert(channel_id=channel_id, twitch_username=str.lower(twitch_username))

            if custom_message:
                new_user.custom_message = custom_message

            session.add(new_user)
            session.commit()

    async def remove_user_from_ta(self, channel_id, twitch_username):
        """
        Removes a user from a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_username: The Twitch username of the user to be added
        :return:
        """
        with session_manager() as session:
            message = session.execute(select(UserInTwitchAlert)
                                      .filter_by(twitch_username=twitch_username, channel_id=channel_id)
                                      ).scalars().one_or_none()
            if message is not None:
                await self.delete_message(message.message_id, channel_id)
                session.delete(message)
                session.commit()

    async def delete_message(self, message_id, channel_id):
        """
        Deletes a given discord message
        :param message_id: discord message ID of the message to delete
        :param channel_id: discord channel ID which has the message
        :return:
        """
        with session_manager() as session:
            try:
                channel = self.bot.get_channel(int(channel_id))
                if channel is None:
                    logger.warning(f"TwitchAlert: Channel ID {channel_id} does not exist, removing from database")
                    sql_remove_invalid_channel = delete(TwitchAlerts).where(TwitchAlerts.channel_id == channel_id)
                    session.execute(sql_remove_invalid_channel)
                    session.commit()
                    return
                message = await channel.fetch_message(message_id)
                await message.delete()
            except discord.errors.NotFound as err:
                logger.warning(f"TwitchAlert: Message ID {message_id} does not exist, skipping \nError: {err}")
            except discord.errors.Forbidden as err:
                logger.warning(f"TwitchAlert: {err}  Channel ID: {channel_id}")
                sql_remove_invalid_channel = delete(TwitchAlerts).where(TwitchAlerts.channel_id == channel_id)
                session.execute(sql_remove_invalid_channel)
                session.commit()

    def get_users_in_ta(self, channel_id):
        """
        Returns all users in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the users
        """
        sql_get_users = select(UserInTwitchAlert.twitch_username).filter_by(channel_id=channel_id)
        with session_manager() as session:
            return session.execute(sql_get_users).all()

    def get_teams_in_ta(self, channel_id):
        """
        Returns all teams in a given Twitch Alert
        :param channel_id: The channel ID of the Twitch Alert
        :return: The sql results of the teams
        """
        sql_get_teams = select(TeamInTwitchAlert.twitch_team_name).filter_by(channel_id=channel_id)
        with session_manager() as session:
            return session.execute(sql_get_teams).all()

    def add_team_to_ta(self, channel_id, twitch_team, custom_message, guild_id=None):
        """
        Add a twitch team to a given Twitch Alert
        :param channel_id: The discord channel ID of the twitch Alert
        :param twitch_team: The Twitch team to be added
        :param custom_message: The custom Message of the team's live notification.
            None = use default Twitch Alert message
        :param guild_id: The guild ID of the channel
        :return:
        :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
        """
        self.new_ta(guild_id, channel_id)
        with session_manager() as session:
            new_team = TeamInTwitchAlert(channel_id=channel_id, twitch_team_name=str.lower(twitch_team))

            if custom_message:
                new_team.custom_message = custom_message

            session.add(new_team)
            session.commit()

    async def remove_team_from_ta(self, channel_id, team_name):
        """
        Removes a team from a given twitch alert
        :param channel_id: The channel ID of the Twitch Alert
        :param team_name: The team name of the team to be removed
        :return:
        """
        with session_manager() as session:
            team = session.execute(select(TeamInTwitchAlert)
                                   .filter_by(twitch_team_name=team_name, channel_id=channel_id)
                                   ).scalars().one_or_none()
            if not team:
                raise AttributeError("Team name not found")

            users = session.execute(select(UserInTwitchTeam)
                                    .filter_by(team_twitch_alert_id=team.team_twitch_alert_id)).scalars().all()
            if users is not None:
                for user in users:
                    if user.message_id is not None:
                        await self.delete_message(user.message_id, channel_id)
                    session.delete(user)

            session.delete(team)
            session.commit()

    def update_team_members(self, twitch_team_id, team_name):
        """
        Users in a team are updated to ensure they are assigned to the correct team
        :param twitch_team_id: the team twitch alert id
        :param team_name: the name of the team
        :return:
        """
        if re.search(TWITCH_USERNAME_REGEX, team_name):
            users = self.twitch_handler.get_team_users(team_name)
            for user_info in users:
                with session_manager() as session:
                    user = session.execute(
                        select(UserInTwitchTeam)
                        .filter_by(team_twitch_alert_id=twitch_team_id, twitch_username=user_info.get("user_login")))\
                        .scalars()\
                        .one_or_none()

                    if user is None:
                        session.add(UserInTwitchTeam(
                            team_twitch_alert_id=twitch_team_id, twitch_username=user_info.get("user_login")))
                        session.commit()

    def update_all_teams_members(self):
        """
        Updates all teams with the current team members
        :return:
        """
        with session_manager() as session:
            teams_info = session.execute(select(TeamInTwitchAlert)).scalars().all()

        for team_info in teams_info:
            self.update_team_members(team_info.team_twitch_alert_id, team_info.twitch_team_name)

    async def delete_all_offline_team_streams(self, usernames):
        """
        A method that deletes all currently offline streams
        :param usernames: The usernames of the team members
        :return:
        """
        with session_manager() as session:
            results = session.execute(
                select(UserInTwitchTeam).where(
                    and_(
                        UserInTwitchTeam.message_id != null(),
                        UserInTwitchTeam.twitch_username.in_(usernames))
                    ).options(
                        selectinload(UserInTwitchTeam.team)
                    )
            ).scalars().all()

            if results is None:
                return
            for result in results:
                await self.delete_message(result.message_id, result.team.channel_id)
                result.message_id = None

            session.commit()

    async def delete_all_offline_streams(self, usernames):
        """
        A method that deletes all currently offline streams
        :param usernames: The usernames of the twitch members
        :return:
        """
        with session_manager() as session:
            results = session.execute(
                select(
                    UserInTwitchAlert
                ).where(
                    and_(
                        UserInTwitchAlert.message_id != null(),
                        UserInTwitchAlert.twitch_username.in_(usernames)))
            ).scalars().all()

            if results is None:
                return
            for result in results:
                await self.delete_message(result.message_id, result.channel_id)
                result.message_id = None
            session.commit()

    # def translate_names_to_ids(self):
    #     """
    #     Translates usernames and team_names to twitch unique IDs
    #     """
    #     # todo: Create a backup before
    #     with session_manager() as session:
    #         if len(session.execute("SELECT name "
    #                            "FROM sqlite_master "
    #                            "WHERE type='table' AND (name='UserInTwitchAlert' OR name='TeamInTwitchAlert');"
    #                            ).all()) == 0:
    #             return
    #
    #     table_name = "UserInTwitchAlert"
    #     fields = self.db_execute_select(f"PRAGMA table_info({table_name});")
    #     if fields[1][1] == 'twitch_username':
    #         self.user_names_to_ids()
    #     elif fields[1][1] != 'twitch_user_id':
    #         raise NameError(f"Unexpected field {fields[1][1]} in ")
    #
    #     table_name = "TeamInTwitchAlert"
    #     fields = self.db_execute_select(f"PRAGMA table_info({table_name});")
    #     if fields[2][1] == 'twitch_team_name':
    #         self.team_names_to_ids()
    #     elif fields[2][1] != 'twitch_team_id':
    #         raise NameError(f"Unexpected field {fields[1][1]} in ")
    #
    #     # todo: remove all current messages from UserInTwitchTeam & update from empty
    #
    # def user_names_to_ids(self):
    #     with session_manager() as session:
    #         users_in_twitch_alert = session.execute(select(UserInTwitchAlert)).all()
    #         for user in users_in_twitch_alert:
    #             try:
    #                 session.execute(update(UserInTwitchAlert).where(
    #                     UserInTwitchAlert.twitch_username == user.twitch_username).values(
    #                     twitch_username=(self.twitch_handler.get_user_data(usernames=[user.twitch_username]))[0].get("id")))
    #                 session.commit()
    #             except Exception as err:
    #                 logger.error(f"User not found on Twitch {user}, deleted")
    #         session.execute("ALTER TABLE UserInTwitchAlert RENAME COLUMN twitch_username TO twitch_user_id")
    #         session.commit()
    #
    # def team_names_to_ids(self):
    #     with session_manager() as session:
    #         team_in_twitch_alert = session.execute(select(TeamInTwitchAlert)).all()
    #         for team in team_in_twitch_alert:
    #             try:
    #                 session.execute(update(TeamInTwitchAlert).where(
    #                     TeamInTwitchAlert == team.twitch_team_name).values(
    #                     twitch_team_name=self.twitch_handler.get_team_data(team.twitch_team_name).get("id")))
    #                 session.commit()
    #             except Exception as err:
    #                 logger.error(f"Team not found on Twitch {team}, deleted")
    #         session.execute("ALTER TABLE TeamInTwitchAlert RENAME COLUMN twitch_team_name TO twitch_team_id")
    #         session.commit()
