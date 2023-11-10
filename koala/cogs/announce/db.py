# Built-in/Generic Imports
from sqlalchemy import select

# Own modules
from koala.db import session_manager
from .models import GuildUsage


# Libs


class AnnounceDBManager:
    """
    A class for interacting with the KoalaBot announcement database
    """
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
                session.add(guild_usage)
            else:
                guild_usage.last_message_epoch_time = last_time
            session.commit()
