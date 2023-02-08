import time

import discord
from discord.ext.commands import Bot
from sqlalchemy import select, func, or_, and_, null, update, delete

from .log import logger
from .models import UserInTwitchTeam, TeamInTwitchAlert, TwitchAlerts, UserInTwitchAlert
from koala.db import assign_session
from koala.models import GuildExtensions


@assign_session
async def create_team_alerts(bot: Bot, ta_database_manager, session):
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

    streams_data = ta_database_manager.twitch_handler.get_streams_data(usernames)

    if streams_data is None:
        return

    for stream_data in streams_data:
        try:
            if stream_data.get('type') == "live":
                current_username = str.lower(stream_data.get("user_login"))
                logger.debug("Creating team stream alert for %s" % current_username)
                old_len = len(usernames)
                usernames.remove(current_username)
                if len(usernames) == old_len:
                    logger.error(f"TwitchAlert: {stream_data.get('user_login')} not found in the user teams list")
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

                                new_message_embed = await ta_database_manager.create_alert_embed(stream_data, message)

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
    await ta_database_manager.delete_all_offline_team_streams(usernames)
    time_diff = time.time() - start
    if time_diff > 5:
        logger.warning(f"TwitchAlert: Teams Loop Finished in > 5s | {time_diff}s")


@assign_session
async def create_user_alerts(bot: Bot, ta_database_manager, session):
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

    user_streams = ta_database_manager.twitch_handler.get_streams_data(usernames)
    if user_streams is None:
        return

    # Deals with online streams
    for streams_details in user_streams:
        try:
            if streams_details.get('type') == "live":
                current_username = str.lower(streams_details.get("user_login"))
                old_len = len(usernames)
                usernames.remove(current_username)
                if len(usernames) == old_len:
                    logger.error(f"TwitchAlert: {streams_details.get('user_login')} not found in the user list")

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
    await ta_database_manager.delete_all_offline_streams(usernames)
    time_diff = time.time() - start
    if time_diff > 5:
        logger.warning(f"TwitchAlert: User Loop Finished in > 5s | {time_diff}s")

