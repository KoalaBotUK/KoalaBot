#!/usr/bin/env python

"""
new Koala Bot database manager

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os

# Libs
from pathlib import Path
from sqlalchemy import select, update, insert


# Own modules
from utils.base_models import KoalaExtensions, GuildExtensions
from utils.KoalaUtils import session, Base, engine, ENCRYPTED_DB, DATABASE_PATH

# Constants

# Variables


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

    sql_check_extension_exists = select(KoalaExtensions).where(KoalaExtensions.extension_id == extension_id)

    if len(session.execute(sql_check_extension_exists).all()) > 0:
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

    result = session.execute(sql_select_extension).all()
    return len(list(filter(lambda x: x.extension_id in ["All", extension_id], result))) > 0


def __create_db(file_path):
    """
    Creates the database, with correct permissions on unix
    :param file_path: The file path of the database
    """
    Path(file_path).touch()
    if ENCRYPTED_DB:
        os.system("chown www-data "+file_path)
        os.system("chmod 777 "+file_path)


def __create_tables():
    """
    Creates all tables currently in the metadata of Base
    """
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)


def setup():
    """
    Creates the database and tables
    """
    __create_db(DATABASE_PATH)
    __create_tables()
