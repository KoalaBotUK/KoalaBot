# Built-in/Generic Imports
import re
from sqlalchemy import select, delete, and_, null
from sqlalchemy.orm import selectinload

# Own modules
from koala.utils import KoalaDBManager
from koala.db import setup, session_manager, DATABASE_PATH
from koala.env import DB_KEY

from .models import GuildUsage
from .utils import ANNOUNCE_SEPARATION_DAYS, SECONDS_IN_A_DAY, TIMEOUT_TIME, MAX_MESSAGE_LENGTH
from .log import logger


# Libs
import discord



class AnnounceDBManager:
    """
    A class for interacting with the KoalaBot announcement database
    """

    def __init__(self):
        """
        initiate variables
        :param database_manager:
        """
        setup()

    def get_last_use_date(self, guild_id: int):
        """
        Gets the last time when this function was used
        :param guild_id: id of the target guild
        :return:
        """
        with session_manager() as session:
            usage = session.execute(
                select(GuildUsage.last_message_epoch_time).filter_by(guild_id=guild_id)).one_or_none()
            if usage:
                return usage.last_message_epoch_time
            else:
                return None

    def set_last_use_date(self, guild_id: int, last_time: int):
        """
        Set the last time when this function was used
        :param guild_id: id of the guild
        :param last_time: time when the function was used
        :return:
        """
        with session_manager() as session:
            guild_usage = session.execute(select(GuildUsage).filter_by(guild_id=guild_id)).scalars().one_or_none()
            if not guild_usage:
                guild_usage = GuildUsage(guild_id=guild_id, last_message_epoch_time=last_time)
            else:
                guild_usage.last_message_epoch_time = last_time
            session.add(guild_usage)
            session.commit()
