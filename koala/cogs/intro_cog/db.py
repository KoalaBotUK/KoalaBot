# Futures

# Built-in/Generic Imports
import re

# Libs
import discord
from sqlalchemy import select, update

# Own modules
from koala.db import session_manager

from .models import GuildWelcomeMessages
from .utils import DEFAULT_WELCOME_MESSAGE, BASE_LEGAL_MESSAGE

# Constants

# Variables


def fetch_guild_welcome_message(guild_id):
    """
    Fetches the guild welcome message for a given guild

    :param guild_id: Discord guild ID for a given server
    """
    with session_manager() as session:
        msg = session.execute(select(GuildWelcomeMessages.welcome_message)
                              .where(GuildWelcomeMessages.guild_id == guild_id)).one_or_none()
    if not msg:
        return None
    else:
        return msg.welcome_message


def update_guild_welcome_message(guild_id, new_message: str):
    """
    Update guild welcome message for a given guild

    :param guild_id: Discord guild ID for a given server
    :param new_message: The new guild welcome message to be set
    """
    with session_manager() as session:
        session.execute(update(GuildWelcomeMessages)
                        .where(GuildWelcomeMessages.guild_id == guild_id)
                        .values(welcome_message=new_message))
        session.commit()
    return new_message


def remove_guild_welcome_message(guild_id):
    """
    Removes the guild welcome message from a given guild

    :param guild_id: Discord guild ID for a given server
    """
    with session_manager() as session:
        welcome_message = session.execute(select(GuildWelcomeMessages).filter_by(guild_id=guild_id))\
            .scalars().one_or_none()
        if welcome_message:
            session.delete(welcome_message)
            session.commit()
            return 1
        return 0


def new_guild_welcome_message(guild_id):
    """
    Sets the default guild welcome message to a given guild

    :param guild_id: Discord guild ID for a given server
    """

    with session_manager() as session:
        session.add(GuildWelcomeMessages(guild_id=guild_id, welcome_message=DEFAULT_WELCOME_MESSAGE))
        session.commit()
    return fetch_guild_welcome_message(guild_id)


def get_guild_welcome_message(guild_id: int):
    """
    Retrieves a guild's customised welcome message from the database. Includes the basic legal message constant
    :param guild_id: ID of the guild
    :return: The particular guild's welcome message : str
    """
    msg = fetch_guild_welcome_message(guild_id)
    if msg is None:
        msg = new_guild_welcome_message(guild_id)
    return f"{msg}\r\n{BASE_LEGAL_MESSAGE}"
