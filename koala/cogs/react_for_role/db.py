#!/usr/bin/env python

# Built-in/Generic Imports
from typing import *

import sqlalchemy.exc
import sqlalchemy.orm
from sqlalchemy import select, delete, and_

# Own modules
from koala.db import session_manager
from .log import logger
from .models import GuildRFRMessages, RFRMessageEmojiRoles, GuildRFRRequiredRoles
from koala.db import assign_session

@assign_session
def add_rfr_message(guild_id: int, channel_id: int, message_id: int, session: sqlalchemy.orm.Session):
    """
    Add an rfr message to a guild. Table stores a unique emoji_role_id to prevent the same combination
    appearing twice on a given message
    :param guild_id: ID of the guild
    :param channel_id: ID of the channel the rfr message is in
    :param message_id: ID of the rfr message
    :return:
    """
    session.add(
        GuildRFRMessages(guild_id=guild_id, channel_id=channel_id, message_id=message_id))
    session.commit()

@assign_session
def add_rfr_message_emoji_role(emoji_role_id: int, emoji_raw: str, role_id: int, session: sqlalchemy.orm.Session):
    """
    Add an emoji-role combination to an rfr message.
    :param emoji_role_id: unique ID/key
    :param emoji_raw: raw emoji representation in string format
    :param role_id: ID of the role to give on react
    :return:
    """
    try:
        session.add(RFRMessageEmojiRoles(emoji_role_id=emoji_role_id, emoji_raw=emoji_raw, role_id=role_id))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        logger.warning("RFRMessageEmojiRoles already exists for <%s, %s, %s>, continuing",
                        emoji_role_id, emoji_raw, role_id)

@assign_session
def remove_rfr_message_emoji_role(emoji_role_id: int, emoji_raw: str = None, role_id: int = None, session: sqlalchemy.orm.Session = None):
    """
    Remove an emoji-role combination from the rfr message database. Uses the unique emoji_role_id to identify the
    specific combo. Only removes one emoji-role combo
    :param emoji_role_id: unique ID/key
    :param emoji_raw: raw string representation of the emoji
    :param role_id: ID of the role to give on react
    :return:
    """
    if not emoji_raw:
        delete_sql = delete(RFRMessageEmojiRoles)\
            .where(
            and_(
                RFRMessageEmojiRoles.emoji_role_id == emoji_role_id,
                RFRMessageEmojiRoles.role_id == role_id
            ))
    else:
        delete_sql = delete(RFRMessageEmojiRoles)\
            .where(
            and_(
                RFRMessageEmojiRoles.emoji_role_id == emoji_role_id,
                RFRMessageEmojiRoles.emoji_raw == emoji_raw
            ))
    session.execute(delete_sql)
    session.commit()

@assign_session
def remove_rfr_message_emoji_roles(emoji_role_id: int, session: sqlalchemy.orm.Session):
    """
    Removes all emoji-role combos with the same emoji_role_id i.e. on the same message.
    :param emoji_role_id: unique ID/key
    :return:
    """
    delete_sql = delete(RFRMessageEmojiRoles) \
        .where(RFRMessageEmojiRoles.emoji_role_id == emoji_role_id)

    session.execute(delete_sql)
    session.commit()

@assign_session
def remove_rfr_message(guild_id: int, channel_id: int, message_id: int, session: sqlalchemy.orm.Session):
    """
    Removes an rfr message from the rfr message database, and also removes all emoji-role combos as part of it.
    :param guild_id: Guild ID of the rfr message
    :param channel_id: Channel ID of the rfr message
    :param message_id: Message ID of the rfr message
    :return:
    """
    emoji_role_id = get_rfr_message(guild_id, channel_id, message_id)
    if not emoji_role_id:
        return
    else:
        remove_rfr_message_emoji_roles(emoji_role_id[3])

    delete_sql = delete(GuildRFRMessages) \
        .where(and_(and_(
                GuildRFRMessages.guild_id == guild_id,
                GuildRFRMessages.channel_id == channel_id),
                GuildRFRMessages.message_id == message_id))
    session.execute(delete_sql)
    session.commit()

@assign_session
def get_rfr_message(guild_id: int, channel_id: int, message_id: int, session: sqlalchemy.orm.Session) -> Optional[Tuple[int, int, int, int]]:
    """
    Gets the unique rfr message that is specified by the guild ID, channel ID and message ID.
    :param guild_id: Guild ID of the rfr message
    :param channel_id: Channel ID of the rfr message
    :param message_id: Message ID of the rfr message
    :return: RFR message info of the specific message if found, otherwise None.
    """
    message = session.execute(select(GuildRFRMessages)
                                .filter_by(guild_id=guild_id,
                                            channel_id=channel_id,
                                            message_id=message_id)).scalars().one_or_none()
    if message:
        return message.old_format()
    else:
        return None

@assign_session
def get_guild_rfr_messages(guild_id: int, session: sqlalchemy.orm.Session) -> List[Tuple[int, int, int]]:
    """
    Gets all rfr messages in a given guild, from the guild ID
    :param guild_id: ID of the guild
    :return: List of rfr messages in the guild.
    """
    messages = session.execute(select(GuildRFRMessages)
                                .filter_by(guild_id=guild_id)).scalars().all()
    return [message.old_format()
            for message in messages]

@assign_session
def get_guild_rfr_roles(guild_id: int) -> List[int]:
    """
    Returns all role IDs of roles given by RFR messages in a guild

    :param guild_id: Guild ID to check in.
    :return: Role IDs of RFR roles in a specific guild
    """
    with session_manager() as session:
        rfr_messages = session.execute(select(GuildRFRMessages).filter_by(guild_id=guild_id)).scalars().all()
        if not rfr_messages:
            return []
        role_ids: List[int] = []
        for rfr_message in rfr_messages:
            roles: List[Tuple[int, str, int]] = get_rfr_message_emoji_roles(rfr_message.emoji_role_id)
            if not roles:
                continue
            ids: List[int] = [x[2] for x in roles]
            role_ids.extend(ids)
        return role_ids

@assign_session
def get_rfr_message_emoji_roles(emoji_role_id: int, session: sqlalchemy.orm.Session):
    """
    Returns all the emoji-role combinations on an rfr message

    :param emoji_role_id: emoji-role combo identifier
    :return: List of rows in the database if found, otherwise None
    """
    with session_manager() as session:
        rows = session.execute(select(RFRMessageEmojiRoles).filter_by(emoji_role_id=emoji_role_id)).scalars().all()

        return [(row.emoji_role_id, row.emoji_raw, row.role_id) for row in rows]

@assign_session
def get_rfr_reaction_role(emoji_role_id: int, emoji_raw: str, role_id: int):
    """
    Returns a specific emoji-role combo on an rfr message

    :param emoji_role_id: emoji-role combo identifier
    :param emoji_raw: raw string representation of the emoji
    :param role_id: role ID of the emoji-role combo
    :return: Unique row corresponding to a specific emoji-role combo
    """
    with session_manager() as session:
        row = session.execute(select(RFRMessageEmojiRoles).filter_by(
            emoji_role_id=emoji_role_id, emoji_raw=emoji_raw, role_id=role_id)).scalar()
        if row:
            return row.emoji_role_id, row.emoji_raw, row.role_id
        else:
            return None

@assign_session
def get_rfr_reaction_role_by_emoji_str(emoji_role_id: int, emoji_raw: str) -> Optional[int]:
    """
    Gets a role ID from the emoji_role_id and the emoji associated with that role in the emoji-role combo
    :param emoji_role_id: emoji-role combo identifier
    :param emoji_raw: raw string representation of the emoji
    :return: role ID of the emoji-role combo
    """
    with session_manager() as session:
        row = session.execute(select(RFRMessageEmojiRoles.role_id)
                                .filter_by(emoji_role_id=emoji_role_id, emoji_raw=emoji_raw)).one_or_none()
        if not row:
            return
        return row[0]

@assign_session
def add_guild_rfr_required_role(guild_id: int, role_id: int, session: sqlalchemy.orm.Session):
    """
    Adds a role to the list of roles required to use rfr functionality in a guild.
    :param guild_id: guild ID
    :param role_id: role ID
    :return:
    """
    session.add(GuildRFRRequiredRoles(guild_id=guild_id, role_id=role_id))
    session.commit()

@assign_session
def remove_guild_rfr_required_role(guild_id: int, role_id: int, session: sqlalchemy.orm.Session):
    """
    Removes a role from the list of roles required to use rfr functionality in a guild
    :param guild_id: guild ID
    :param role_id: role ID
    :return:
    """
    session.execute(delete(GuildRFRRequiredRoles).filter_by(guild_id=guild_id, role_id=role_id))
    session.commit()

@assign_session
def get_guild_rfr_required_roles(guild_id, session: sqlalchemy.orm.Session) -> List[int]:
    """
    Gets the list of role IDs of roles required to use rfr functionality in a guild
    :param guild_id: guild ID
    :return: List of role IDs
    """
    rows = session.execute(select(GuildRFRRequiredRoles).filter_by(guild_id=guild_id)).scalars().all()

    role_ids = [x.role_id for x in rows]
    if not role_ids:
        return []
    return role_ids
