# Futures
# Built-in/Generic Imports

# Libs
import discord
import sqlalchemy.orm
from sqlalchemy import select, update

# Own modules
from koala.db import assign_session
from .models import GuildWelcomeMessages
from .utils import DEFAULT_WELCOME_MESSAGE, BASE_LEGAL_MESSAGE, dm_group_message, get_non_bot_members
from .log import logger

# Constants

# Variables






@assign_session
def new_guild_welcome_message(guild_id, *, session: sqlalchemy.orm.Session):
    """
    Sets the default guild welcome message to a given guild

    :param guild_id: Discord guild ID for a given server
    :param session:
    """

    session.add(GuildWelcomeMessages(guild_id=guild_id, welcome_message=DEFAULT_WELCOME_MESSAGE))
    session.commit()
    logger.info(f"Setup new welcome message for guild, id = {guild_id}.")
    return fetch_guild_welcome_message(guild_id, session=session)


@assign_session
async def send_member_welcome_message(member: discord.Member, **kwargs):
    await member.send(get_guild_welcome_message(member.guild.id, **kwargs))
    logger.info(f"Sent member {member.name} a welcome message for guild {member.guild.id}.")


@assign_session
def remove_guild_welcome_message(guild_id, *, session: sqlalchemy.orm.Session):
    """
    Removes the guild welcome message from a given guild

    :param guild_id: Discord guild ID for a given server
    :param session:
    """
    welcome_message = session.execute(select(GuildWelcomeMessages).filter_by(guild_id=guild_id)).scalar()
    if welcome_message:
        session.delete(welcome_message)
        logger.info(f"KoalaBot left guild, id = {guild_id}. Deleted welcome message.")
        session.commit()
        return 1
    return 0


@assign_session
async def send_all_members_welcome_messages(guild, **kwargs):
    non_bot_members = get_non_bot_members(guild)
    await dm_group_message(non_bot_members, get_guild_welcome_message(guild.id, **kwargs))


@assign_session
def update_guild_welcome_message(guild_id, new_message: str, *, session: sqlalchemy.orm.Session):
    """
    Update guild welcome message for a given guild

    :param guild_id: Discord guild ID for a given server
    :param new_message: The new guild welcome message to be set
    :param session:
    """
    session.execute(update(GuildWelcomeMessages)
                    .where(GuildWelcomeMessages.guild_id == guild_id)
                    .values(welcome_message=new_message))
    session.commit()
    return new_message


@assign_session
def get_guild_welcome_message(guild_id: int, **kwargs):
    """
    Retrieves a guild's customised welcome message from the database. Includes the basic legal message constant
    :param guild_id: ID of the guild
    :return: The particular guild's welcome message : str
    """
    msg = fetch_guild_welcome_message(guild_id, **kwargs)
    if msg is None:
        msg = new_guild_welcome_message(guild_id, **kwargs)
    return f"{msg}\n\r{BASE_LEGAL_MESSAGE}"


@assign_session
def fetch_guild_welcome_message(guild_id, *, session: sqlalchemy.orm.Session):
    """
    Fetches the guild welcome message for a given guild

    :param guild_id: Discord guild ID for a given server
    :param session:
    """
    return session.execute(select(GuildWelcomeMessages.welcome_message)
                           .where(GuildWelcomeMessages.guild_id == guild_id)).scalar()
