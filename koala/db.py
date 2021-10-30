#!/usr/bin/env python

"""
new Koala Bot database manager

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
from contextlib import contextmanager

# Libs
from pathlib import Path
from sqlalchemy import select, update, insert, delete, and_, func, create_engine
from sqlalchemy.orm import sessionmaker


# Own modules
from koala.models import Base, KoalaExtensions, GuildExtensions, GuildWelcomeMessages
from koala.env import DB_KEY, ENCRYPTED_DB
from koala.utils.KoalaUtils import get_arg_config_path, format_config_path

# Constants

# Variables


def _get_sql_url(db_path, encrypted: bool, db_key=None):
    if encrypted:
        return "sqlite+pysqlcipher://:x'" + db_key + "'@/" + db_path
    else:
        return "sqlite:///" + db_path

def setup():
    """
    Creates the database and tables
    """
    __create_db(DATABASE_PATH)
    __create_tables()


def __create_db(file_path):
    """
    Creates the database, with correct permissions on unix
    :param file_path: The file path of the database
    """
    Path(get_arg_config_path()).mkdir(exist_ok=True)
    Path(file_path).touch()
    if ENCRYPTED_DB:
        os.system("chown www-data "+file_path)
        os.system("chmod 777 "+file_path)


def __create_tables():
    """
    Creates all tables currently in the metadata of Base
    """
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)


def insert_extension(extension_id: str, subscription_required: int, available: bool, enabled: bool):
    """
    Inserts a Koala Extension into the KoalaExtensions table

    :param extension_id: The unique extension ID/ name
    :param subscription_required: The required subscription level to unlock this extension
    :param available: Is available to be enabled by the public
        (false for if a special extension is to be enabled in one server only by the devs)
    :param enabled: Is currently enabled and running
        (false if down for maintenance)
    """

    sql_check_extension_exists = select(func.count(KoalaExtensions.extension_id))\
        .where(KoalaExtensions.extension_id == extension_id)

    with session_manager() as session:
        if session.execute(sql_check_extension_exists).scalars().one() > 0:
            sql_update_extension = update(KoalaExtensions)\
                .where(KoalaExtensions.extension_id == extension_id)\
                .values(
                    subscription_required=subscription_required,
                    available=available,
                    enabled=enabled)
        else:
            sql_update_extension = insert(KoalaExtensions)\
                .values(
                    extension_id=extension_id,
                    subscription_required=subscription_required,
                    available=available,
                    enabled=enabled)

        session.execute(sql_update_extension)
        session.commit()


def extension_enabled(guild_id, extension_id: str):
    """
    Check if a given extension is enabled in a specific guild

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID
    """
    sql_select_extension = select(GuildExtensions.extension_id)\
        .where(GuildExtensions.guild_id == guild_id)

    with session_manager() as session:
        result = session.execute(sql_select_extension).all()
    return len(list(filter(lambda x: x.extension_id in ["All", extension_id], result))) > 0


def give_guild_extension(guild_id, extension_id: str):
    """
    Give a guild the given Koala extension

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID

    :raises NotImplementedError: extension_id doesnt exist
    """
    with session_manager() as session:
        sql_check_extension_exists = select(KoalaExtensions)\
            .where(and_(KoalaExtensions.extension_id == extension_id, KoalaExtensions.available == 1))
        result = session.execute(sql_check_extension_exists).all()
        if len(result) > 0 or extension_id == "All":
            sql_insert_guild_extension = insert(GuildExtensions)\
                .values(extension_id=extension_id, guild_id=guild_id).prefix_with("OR IGNORE")
            session.execute(sql_insert_guild_extension)
            session.commit()
        else:
            raise NotImplementedError(f"{extension_id} is not a valid extension")


def remove_guild_extension(guild_id, extension_id: str):
    """
    Remove a given Koala extension from a guild

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID
    """
    sql_remove_extension = delete(GuildExtensions)\
        .where(
        and_(
            GuildExtensions.extension_id == extension_id,
            GuildExtensions.guild_id == guild_id))
    with session_manager() as session:
        session.execute(sql_remove_extension)
        session.commit()


def get_enabled_guild_extensions(guild_id: int):
    """
    Gets a list of extensions IDs that are enabled in a server

    :param guild_id: Discord guild ID for a given server
    """
    sql_select_enabled = select(GuildExtensions.extension_id)\
        .join(KoalaExtensions, GuildExtensions.extension_id == KoalaExtensions.extension_id)\
        .where(
        and_(GuildExtensions.guild_id == guild_id,
             KoalaExtensions.available == 1))
    with session_manager() as session:
        return [extension.extension_id for extension in session.execute(sql_select_enabled).all()]


def get_all_available_guild_extensions(guild_id: int):
    """
    Gets all available guild extensions for a given guild

    todo: restrict with rules of subscriptions & enabled state

    :param guild_id: Discord guild ID for a given server
    """
    sql_select_all = select(KoalaExtensions.extension_id).where(KoalaExtensions.available == 1).distinct()
    with session_manager() as session:
        return [extension.extension_id for extension in session.execute(sql_select_all).all()]


def fetch_all_tables():
    """
    Fetches all table names within the database
    """
    with session_manager() as session:
        return [table.name for table in
                session.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").all()]


def clear_all_tables(tables):
    """
    Clears al the data from the given tables

    :param tables: a list of all tables to be cleared
    """
    with session_manager() as session:
        for table in tables:
            session.execute('DELETE FROM ' + table + ';')
            session.commit()


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
        rows = session.execute(select(GuildWelcomeMessages).where(GuildWelcomeMessages.guild_id == guild_id)).all()
        session.execute(delete(GuildWelcomeMessages).where(GuildWelcomeMessages.guild_id == guild_id))
        session.commit()
    return len(rows)


def new_guild_welcome_message(guild_id):
    """
    Sets the default guild welcome message to a given guild

    :param guild_id: Discord guild ID for a given server
    """
    from koala.cogs.IntroCog import DEFAULT_WELCOME_MESSAGE

    with session_manager() as session:
        session.execute(insert(GuildWelcomeMessages).values(guild_id=guild_id, welcome_message=DEFAULT_WELCOME_MESSAGE))
        session.commit()
    return fetch_guild_welcome_message(guild_id)


CONFIG_DIR = get_arg_config_path()
DATABASE_PATH = format_config_path(CONFIG_DIR, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")

engine = create_engine(_get_sql_url(db_path=DATABASE_PATH,
                                    encrypted=ENCRYPTED_DB,
                                    db_key=DB_KEY), future=True)
Session = sessionmaker(future=True)
Session.configure(bind=engine)


@contextmanager
def session_manager():
    """
    Provide a transactional scope around a series of operations
    """
    session = Session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()