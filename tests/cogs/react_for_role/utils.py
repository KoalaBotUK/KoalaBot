#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
from typing import *

# Libs
import sqlalchemy.orm
from sqlalchemy import select

# Own modules
from koala.cogs.react_for_role.models import GuildRFRRequiredRoles, GuildRFRMessages, RFRMessageEmojiRoles


def independent_get_guild_rfr_message(session: sqlalchemy.orm.Session, guild_id=None, channel_id=None, message_id=None
                                      ) -> List[Tuple[int, int, int, int]]:
    sql_select = select(GuildRFRMessages)
    if guild_id is not None:
        sql_select = sql_select.filter_by(guild_id=guild_id)
    if channel_id is not None:
        sql_select = sql_select.filter_by(channel_id=channel_id)
    if message_id is not None:
        sql_select = sql_select.filter_by(message_id=message_id)
    rows = session.execute(sql_select).scalars()
    return [row.old_format() for row in rows]


def independent_get_rfr_message_emoji_role(session: sqlalchemy.orm.Session, emoji_role_id=None, emoji_raw=None,
                                           role_id=None) -> List[
    Tuple[int, str, int]]:
    sql_select = select(RFRMessageEmojiRoles)
    if emoji_role_id is not None:
        sql_select = sql_select.filter_by(emoji_role_id=emoji_role_id)
    if emoji_raw is not None:
        sql_select = sql_select.filter_by(emoji_raw=emoji_raw)
    if role_id is not None:
        sql_select = sql_select.filter_by(role_id=role_id)

    rows = session.execute(sql_select).scalars().all()
    return [(row.emoji_role_id, row.emoji_raw, row.role_id) for row in rows]


def independent_get_guild_rfr_required_role(session: sqlalchemy.orm.Session, guild_id=None, role_id=None
                                            ) -> List[Tuple[int, int]]:
    sql_select = select(GuildRFRRequiredRoles)
    if guild_id is not None:
        sql_select = sql_select.filter_by(guild_id=guild_id)
    if role_id is not None:
        sql_select = sql_select.filter_by(role_id=role_id)
    rows = session.execute(sql_select).scalars().all()

    return [(row.guild_id, row.role_id) for row in rows]


def get_rfr_reaction_role_by_role_id(session: sqlalchemy.orm.Session, emoji_role_id: int, role_id: int
                                     ) -> Optional[int]:
    row = session.execute(select(RFRMessageEmojiRoles.role_id)
                          .filter_by(emoji_role_id=emoji_role_id, role_id=role_id)).one_or_none()
    if row:
        return row.role_id
    else:
        return
