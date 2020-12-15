#!/usr/bin/env python

"""
KoalaBot Discipline

Author:
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager


# Libs

# Constants


def discipline_is_enabled(ctx):
    """
    A command used to check if the guild has enabled rfr
    e.g. @commands.check(discipline_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Discipline")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class Discipline(commands.Cog):
    """
    A discord.py cog pertaining to a Discipline system for kicking/warning/banning rulebreakers
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("Discipline", 0, True, True)
        self.rfr_database_manager = DisciplineDBManager(KoalaBot.database_manager)
        self.rfr_database_manager.create_tables()


class DisciplineDBManager:
    """
    A class for interacting with the KoalaBot ReactForRole database
    """

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager: KoalaDBManager.KoalaDBManager = database_manager

    def get_parent_database_manager(self):
        """
        Gets the parent database manager, i.e. the KoalaDBManager class this takes from
        :return: parent database manager
        """
        return self.database_manager

    def create_tables(self):
        """
        Creates all the tables associated with the React For Role extension
        """
        sql_create_guild_rfr_message_ids_table = """
        CREATE TABLE IF NOT EXISTS GuildWarnings (
            guild_id integer NOT NULL,
            user_id integer NOT NULL,
            warning_timeout text NOT NULL, 
            warning_reason text,
            primary key (guild_id, user_id, warning_timeout)
        );
        """
        self.database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Discipline(bot))
