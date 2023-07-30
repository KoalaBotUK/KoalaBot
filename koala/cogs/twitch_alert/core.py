import time
import re
from typing import List

import discord
from discord.ext.commands import Bot
from sqlalchemy import select, func, or_, and_, null, update, delete
from sqlalchemy.orm import Session, joinedload
from twitchAPI.object import Stream

from koala.db import assign_session
from koala.models import GuildExtensions
from .log import logger
from .models import UserInTwitchTeam, TeamInTwitchAlert, TwitchAlerts, UserInTwitchAlert
from .twitch_handler import TwitchAPIHandler
from .utils import DEFAULT_MESSAGE, TWITCH_USERNAME_REGEX, create_live_embed

twitch_handler = TwitchAPIHandler()


@assign_session
async def create_team_alerts(bot: Bot, *, session):
    start = time.time()

    sql_select_team_users = select(func.distinct(UserInTwitchTeam.twitch_username)) \
        .join(TeamInTwitchAlert, UserInTwitchTeam.team_twitch_alert_id == TeamInTwitchAlert.team_twitch_alert_id) \
        .join(TwitchAlerts, TeamInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
        .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
        .where(or_(GuildExtensions.extension_id == 'TwitchAlert', GuildExtensions.extension_id == 'All'))
    users = session.execute(sql_select_team_users).all()
    # sql_select_team_users = "SELECT twitch_username, twitch_team_name " \
    #                         "FROM UserInTwitchTeam " \
    #                         "JOIN TeamInTwitchAlert TITA " \
    #                         "  ON UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id " \
    #                         "JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id " \
    #                         "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
    #                         "WHERE extension_id = 'TwitchAlert' " \
    #                         "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id "

    usernames = [str.lower(user[0]) for user in users]

    if not usernames:
        return

    streams: List[Stream] = await twitch_handler.get_streams_data(usernames)

    if streams is None:
        return

    for stream in streams:
        try:
            if stream.type == "live":
                current_username = str.lower(stream.user_login)
                logger.debug("Creating team stream alert for %s" % current_username)
                old_len = len(usernames)
                usernames.remove(current_username)
                if len(usernames) == old_len:
                    logger.error(f"TwitchAlert: {stream.user_login} not found in the user teams list")
                sql_find_message_id = select(TeamInTwitchAlert.channel_id,
                                             UserInTwitchTeam.message_id,
                                             TeamInTwitchAlert.team_twitch_alert_id,
                                             TeamInTwitchAlert.custom_message,
                                             TwitchAlerts.default_message) \
                    .join(TeamInTwitchAlert,
                          UserInTwitchTeam.team_twitch_alert_id == TeamInTwitchAlert.team_twitch_alert_id) \
                    .join(TwitchAlerts, TeamInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
                    .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
                    .where(and_(and_(or_(GuildExtensions.extension_id == 'TwitchAlert',
                                         GuildExtensions.extension_id == 'All'),
                                     UserInTwitchTeam.twitch_username == current_username),
                                UserInTwitchTeam.message_id == null()))

                # sql_find_message_id = """
                # SELECT TITA.channel_id, UserInTwitchTeam.message_id, TITA.team_twitch_alert_id, custom_message,
                #   default_message
                # FROM UserInTwitchTeam
                # JOIN TeamInTwitchAlert TITA on UserInTwitchTeam.team_twitch_alert_id = TITA.team_twitch_alert_id
                # JOIN TwitchAlerts TA on TITA.channel_id = TA.channel_id
                # JOIN (SELECT extension_id, guild_id
                #       FROM GuildExtensions
                #       WHERE extension_id = 'TwitchAlert' OR extension_id = 'All') GE ON TA.guild_id = GE.guild_id
                # WHERE twitch_username = ?"""

                results = session.execute(sql_find_message_id).all()

                new_message_embed = None

                for result in results:
                    channel_id = result.channel_id
                    message_id = result.message_id
                    team_twitch_alert_id = result.team_twitch_alert_id
                    custom_message = result.custom_message
                    channel_default_message = result.default_message
                    channel: discord.TextChannel = bot.get_channel(channel_id)
                    try:
                        # If no Alert is posted
                        if message_id is None:
                            if new_message_embed is None:
                                if custom_message is not None:
                                    message = custom_message
                                else:
                                    message = channel_default_message

                                new_message_embed = await create_alert_embed(stream, message)

                            if new_message_embed is not None and channel is not None:
                                new_message = await channel.send(embed=new_message_embed)

                                sql_update_message_id = update(UserInTwitchTeam) \
                                    .where(and_(UserInTwitchTeam.team_twitch_alert_id == team_twitch_alert_id,
                                                UserInTwitchTeam.twitch_username == current_username)) \
                                    .values(message_id=new_message.id)
                                session.execute(sql_update_message_id)
                                session.commit()
                    except discord.errors.Forbidden as err:
                        logger.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                        sql_remove_invalid_channel = delete(TwitchAlerts).where(
                            TwitchAlerts.channel_id == channel.id)
                        session.execute(sql_remove_invalid_channel)
                        session.commit()
        except Exception as err:
            logger.error(f"TwitchAlert: Team Loop error {err}")

    # Deals with remaining offline streams
    await delete_all_offline_team_streams(bot, usernames, session=session)
    time_diff = time.time() - start
    if time_diff > 5:
        logger.warning(f"TwitchAlert: Teams Loop Finished in > 5s | {time_diff}s")


@assign_session
async def create_user_alerts(bot: Bot, ta_database_manager, *, session):
    start = time.time()
    # logger.info("TwitchAlert: User Loop Started")
    sql_find_users = select(func.distinct(UserInTwitchAlert.twitch_username)) \
        .join(TwitchAlerts, UserInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
        .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
        .where(or_(GuildExtensions.extension_id == 'TwitchAlert', GuildExtensions.extension_id == 'All'))
    # "SELECT twitch_username " \
    #              "FROM UserInTwitchAlert " \
    #              "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
    #              "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
    #              "WHERE extension_id = 'twitch_alert' OR extension_id = 'All') GE on TA.guild_id = GE.guild_id;"
    users = session.execute(sql_find_users).all()

    usernames = [str.lower(user[0]) for user in users]

    if not usernames:
        return

    user_streams: List[Stream] = await ta_database_manager.twitch_handler.get_streams_data(usernames)
    if user_streams is None:
        return

    # Deals with online streams
    for streams_details in user_streams:
        try:
            if streams_details.type == "live":
                current_username = str.lower(streams_details.user_login)
                old_len = len(usernames)
                usernames.remove(current_username)
                if len(usernames) == old_len:
                    logger.error(f"TwitchAlert: {streams_details.user_login} not found in the user list")

                sql_find_message_id = select(UserInTwitchAlert.channel_id,
                                             UserInTwitchAlert.message_id,
                                             UserInTwitchAlert.custom_message,
                                             TwitchAlerts.default_message) \
                    .join(TwitchAlerts, UserInTwitchAlert.channel_id == TwitchAlerts.channel_id) \
                    .join(GuildExtensions, TwitchAlerts.guild_id == GuildExtensions.guild_id) \
                    .where(and_(and_(or_(GuildExtensions.extension_id == 'TwitchAlert',
                                         GuildExtensions.extension_id == 'All'),
                                     UserInTwitchAlert.twitch_username == current_username),
                                UserInTwitchAlert.message_id == null()))
                # "SELECT UserInTwitchAlert.channel_id, message_id, custom_message, default_message " \
                # "FROM UserInTwitchAlert " \
                # "JOIN TwitchAlerts TA on UserInTwitchAlert.channel_id = TA.channel_id " \
                # "JOIN (SELECT extension_id, guild_id FROM GuildExtensions " \
                # "WHERE extension_id = 'TwitchAlert' " \
                # "  OR extension_id = 'All') GE on TA.guild_id = GE.guild_id " \
                # "WHERE twitch_username = ?;"

                results = session.execute(sql_find_message_id).all()

                new_message_embed = None

                for result in results:
                    channel_id = result.channel_id
                    message_id = result.message_id
                    custom_message = result.custom_message
                    channel_default_message = result.default_message

                    channel = bot.get_channel(channel_id)
                    try:
                        # If no Alert is posted
                        if message_id is None:
                            if new_message_embed is None:
                                if custom_message is not None:
                                    message = custom_message
                                else:
                                    message = channel_default_message

                                new_message_embed = await ta_database_manager.create_alert_embed(streams_details,
                                                                                                 message)

                            if new_message_embed is not None and channel is not None:
                                new_message = await channel.send(embed=new_message_embed)
                                sql_update_message_id = update(UserInTwitchAlert).where(and_(
                                    UserInTwitchAlert.channel_id == channel_id,
                                    UserInTwitchAlert.twitch_username == current_username)) \
                                    .values(message_id=new_message.id)
                                session.execute(sql_update_message_id)
                                session.commit()
                    except discord.errors.Forbidden as err:
                        logger.warning(f"TwitchAlert: {err}  Name: {channel} ID: {channel.id}")
                        sql_remove_invalid_channel = delete(TwitchAlerts).where(
                            TwitchAlerts.channel_id == channel.id)
                        session.execute(sql_remove_invalid_channel)
                        session.commit()

        except Exception as err:
            logger.error(f"TwitchAlert: User Loop error {err}")

    # Deals with remaining offline streams
    await ta_database_manager.delete_all_offline_streams(usernames, session=session)
    time_diff = time.time() - start
    if time_diff > 5:
        logger.warning(f"TwitchAlert: User Loop Finished in > 5s | {time_diff}s")


@assign_session
def add_team_to_ta(channel_id, twitch_team, custom_message, guild_id=None, *, session: Session):
    """
    Add a twitch team to a given Twitch Alert
    :param channel_id: The discord channel ID of the twitch Alert
    :param twitch_team: The Twitch team to be added
    :param custom_message: The custom Message of the team's live notification.
        None = use default Twitch Alert message
    :param guild_id: The guild ID of the channel
    :param session: database session
    :return:
    :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
    """
    new_ta(guild_id, channel_id, session=session)
    new_team = TeamInTwitchAlert(channel_id=channel_id, twitch_team_name=str.lower(twitch_team))

    if custom_message:
        new_team.custom_message = custom_message

    session.add(new_team)
    session.commit()


@assign_session
async def remove_team_from_ta(bot: Bot, channel_id, team_name, *, session: Session):
    """
    Removes a team from a given twitch alert
    :param bot: discord bot
    :param channel_id: The channel ID of the Twitch Alert
    :param team_name: The team name of the team to be removed
    :param session: database session
    :return:
    """
    team = session.execute(select(TeamInTwitchAlert)
                           .filter_by(twitch_team_name=team_name, channel_id=channel_id)
                           ).scalars().first()
    if not team:
        raise AttributeError("Team name not found")

    users = session.execute(select(UserInTwitchTeam)
                            .filter_by(team_twitch_alert_id=team.team_twitch_alert_id)).scalars().all()
    if users is not None:
        for user in users:
            if user.message_id is not None:
                await delete_message(bot, user.message_id, channel_id, session=session)
            session.delete(user)

    session.delete(team)
    session.commit()


@assign_session
def new_ta(guild_id, channel_id, default_message=None, replace=False, *, session: Session):
    """
    Creates a new Twitch Alert and gives the default message associated with it
    :param guild_id: The discord guild ID where the Twitch Alert is located
    :param channel_id: The discord channel ID of the twitch Alert
    :param default_message: The default message of users in the Twitch Alert
    :param replace: True if the new ta should replace the current if exists
    :param session: database session
    :return: The new default_message
    """
    # Sets the default message if not provided
    if default_message is None:
        default_message = DEFAULT_MESSAGE
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


@assign_session
def add_user_to_ta(channel_id, twitch_username, custom_message, guild_id, *, session: Session):
    """
    Add a twitch user to a given Twitch Alert
    :param channel_id: The discord channel ID of the twitch Alert
    :param twitch_username: The Twitch username of the user to be added
    :param custom_message: The custom Message of the user's live notification.
        None = use default Twitch Alert message
    :param guild_id: The guild ID of the channel
    :param session: database session
    :return:
    :raises: KeyError if channel ID is not defined in TwitchAlerts and guild_id is not provided
    """
    new_ta(guild_id, channel_id, session=session)
    new_user = UserInTwitchAlert(channel_id=channel_id, twitch_username=str.lower(twitch_username))

    if custom_message:
        new_user.custom_message = custom_message

    session.add(new_user)
    session.commit()


@assign_session
async def remove_user_from_ta(bot: Bot, channel_id, twitch_username, *, session: Session):
    """
    Removes a user from a given Twitch Alert
    :param channel_id: The discord channel ID of the twitch Alert
    :param twitch_username: The Twitch username of the user to be added
    :return:
    """
    message = session.execute(select(UserInTwitchAlert)
                              .filter_by(twitch_username=twitch_username, channel_id=channel_id)
                              ).scalars().first()
    if message is not None:
        if message.message_id:
            await delete_message(bot, message.message_id, channel_id, session=session)
        session.delete(message)
        session.commit()


async def update_team_members(twitch_team_id, team_name, *, session: Session):
    """
    Users in a team are updated to ensure they are assigned to the correct team
    :param twitch_team_id: the team twitch alert id
    :param team_name: the name of the team
    :param session: database session
    :return:
    """
    if re.search(TWITCH_USERNAME_REGEX, team_name):
        users = await twitch_handler.get_team_users(team_name)
        for user_info in users:
            user = session.execute(
                select(UserInTwitchTeam)
                .filter_by(team_twitch_alert_id=twitch_team_id, twitch_username=user_info.user_login)) \
                .scalars() \
                .one_or_none()

            if user is None:
                session.add(UserInTwitchTeam(
                    team_twitch_alert_id=twitch_team_id, twitch_username=user_info.user_login))
                session.commit()


async def update_all_teams_members(*, session: Session):
    """
    Updates all teams with the current team members
    :return:
    """
    teams_info = session.execute(select(TeamInTwitchAlert)).scalars().all()

    for team_info in teams_info:
        await update_team_members(team_info.team_twitch_alert_id, team_info.twitch_team_name, session=session)


def get_default_message(channel_id, session: Session):
    """
    Get the set default message for the twitch alert
    :param channel_id: The discord channel ID of the twitch Alert
    :return: The current default_message
    """
    result = session.execute(
        select(TwitchAlerts.default_message)
        .filter_by(channel_id=channel_id)
    ).one_or_none()
    if result:
        return result.default_message
    else:
        return DEFAULT_MESSAGE


@assign_session
def get_users_in_ta(channel_id, *, session: Session):
    """
    Returns all users in a given Twitch Alert
    :param channel_id: The channel ID of the Twitch Alert
    :param session: database session
    :return: The sql results of the users
    """
    sql_get_users = select(UserInTwitchAlert.twitch_username).filter_by(channel_id=channel_id)
    return session.execute(sql_get_users).all()


@assign_session
def get_teams_in_ta(channel_id, *, session: Session):
    """
    Returns all teams in a given Twitch Alert
    :param channel_id: The channel ID of the Twitch Alert
    :return: The sql results of the teams
    :param session: database session
    """
    sql_get_teams = select(TeamInTwitchAlert.twitch_team_name).filter_by(channel_id=channel_id)
    return session.execute(sql_get_teams).all()


async def delete_all_offline_team_streams(bot, usernames, *, session: Session):
    """
    A method that deletes all currently offline streams
    :param usernames: The usernames of the team members
    :param session: database session
    :return:
    """
    results = session.execute(
        select(UserInTwitchTeam).where(
            and_(
                UserInTwitchTeam.message_id != null(),
                UserInTwitchTeam.twitch_username.in_(usernames))
        ).options(
            joinedload(UserInTwitchTeam.team)
        )
    ).scalars().all()

    if not results:
        return
    logger.debug("Deleting offline streams: %s" % results)
    for result in results:
        if result.team:
            await delete_message(bot, result.message_id, result.team.channel_id, session=session)
            result.message_id = None
        else:
            logger.debug("Result team not found: %s", result)
            logger.debug("Existing teams: %s", session.execute(select(TeamInTwitchAlert)).scalars().all())
            # session.delete(result)
    session.commit()


async def delete_all_offline_streams(bot: Bot, usernames, *, session: Session):
    """
    A method that deletes all currently offline streams
    :param usernames: The usernames of the twitch members
    :param session: database session
    :return:
    """
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
        await delete_message(bot, result.message_id, result.channel_id, session=session)
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

async def create_alert_embed(stream: Stream, message):
    """
    Creates and sends an alert message
    :param stream: The twitch stream data to have in the message
    :param message: The custom message to be added as a description
    :return: The discord message id of the sent message
    """
    user_details = (await twitch_handler.get_user_data(
        stream.user_name))[0]
    game_details = await twitch_handler.get_game_data(
        stream.game_id)
    return create_live_embed(stream, user_details, game_details, message)


### UTIL


async def delete_message(bot: Bot, message_id, channel_id, *, session: Session):
    """
    Deletes a given discord message
    :param bot: discord bot
    :param message_id: discord message ID of the message to delete
    :param channel_id: discord channel ID which has the message
    :param session: database session
    :return:
    """
    try:
        channel = bot.get_channel(int(channel_id))
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
