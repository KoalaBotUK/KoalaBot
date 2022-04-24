#!/usr/bin/env python

"""
Koala Bot Text Filter Code
Created by: Stefan Cooper
"""

# Built-in/Generic Imports

# Libs
import discord
from sqlalchemy import select, delete

# Own modules
from koala.db import session_manager
from .models import TextFilter, TextFilterModeration, TextFilterIgnoreList


class TextFilterDBManager:
    """
    A class for interacting with the Koala text filter database
    """

    def __init__(self, bot_client: discord.client):
        """
        Initialises local variables

        :param bot_client:
        """
        self.bot = bot_client


    def new_mod_channel(self, guild_id, channel_id):
        """
        Adds new filtered word for a guild

        :param guild_id: Guild ID to retrieve filtered words from
        :param channel_id: The new channel for moderation
        :return:
        """
        with session_manager() as session:
            session.add(TextFilterModeration(channel_id=channel_id, guild_id=guild_id))
            session.commit()

    def new_filtered_text(self, guild_id, filtered_text, filter_type, is_regex):
        """
        Adds new filtered word for a guild

        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :param filter_type: The filter type (banned or risky)
        :param is_regex: Boolean if filtered text is regex
        :return:
        """
        with session_manager() as session:
            ft_id = str(guild_id) + filtered_text
            if not self.does_word_exist(ft_id):
                session.add(TextFilter(filtered_text_id=ft_id,
                                       guild_id=guild_id,
                                       filtered_text=filtered_text,
                                       filter_type=filter_type,
                                       is_regex=is_regex))
                session.commit()
                return
            raise Exception("Filtered word already exists")

    def remove_filter_text(self, guild_id, filtered_text):
        """
        Remove filtered word from a guild

        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :return:
        """
        with session_manager() as session:
            ft_id = str(guild_id) + filtered_text
            if self.does_word_exist(ft_id):
                session.execute(delete(TextFilter).filter_by(filtered_text_id=ft_id))
                session.commit()
                return
            raise Exception("Filtered word does not exist")

    def new_ignore(self, guild_id, ignore_type, ignore):
        """
        Add new ignore to database

        :param guild_id: Guild ID to associate ignore to
        :param ignore_type: The type of ignore to add
        :param ignore: Ignore ID to be added
        """
        with session_manager() as session:
            ignore_id = str(guild_id) + str(ignore)
            if not self.does_ignore_exist(ignore_id):
                session.add(TextFilterIgnoreList(ignore_id=ignore_id, guild_id=guild_id,
                                                 ignore_type=ignore_type, ignore=ignore))
                session.commit()
                return
            raise Exception("Ignore already exists")

    def remove_ignore(self, guild_id, ignore):
        """
        Remove ignore from database

        :param guild_id: The guild_id to delete the ignore from
        :param ignore: the ignore id to be deleted
        """
        with session_manager() as session:
            ignore_id = str(guild_id) + str(ignore)
            if self.does_ignore_exist(ignore_id):
                session.execute(delete(TextFilterIgnoreList).filter_by(ignore_id=ignore_id))
                session.commit()
                return
            raise Exception("Ignore does not exist")

    def get_filtered_text_for_guild(self, guild_id):
        """
        Retrieves all filtered words for a specific guild and formats into a nice list of words

        :param guild_id: Guild ID to retrieve filtered words from:
        :return: list of filtered words
        """
        with session_manager() as session:
            rows = session.execute(select(TextFilter).filter_by(guild_id=guild_id)).scalars()
            return [(row.filtered_text, row.filter_type, str(int(row.is_regex))) for row in rows]

    def get_ignore_list_channels(self, guild_id):
        """
        Get lists of ignored channels

        :param guild_id: The guild id to get the list from
        :return: list of ignored channels
        """
        with session_manager() as session:
            rows = session.execute(select(TextFilterIgnoreList.ignore)
                                   .filter_by(guild_id=guild_id, ignore_type="channel")).all()
            return [row[0] for row in rows]

    def get_ignore_list_users(self, guild_id):
        """
        Get lists of ignored users

        :param guild_id: The guild id to get the list from
        :return: list of ignored users
        """
        with session_manager() as session:
            rows = session.execute(select(TextFilterIgnoreList.ignore)
                                   .filter_by(guild_id=guild_id, ignore_type="user")).all()
            return [row[0] for row in rows]

    def get_all_ignored(self, guild_id):
        with session_manager() as session:
            rows = session.execute(select(TextFilterIgnoreList.ignore_id, TextFilterIgnoreList.guild_id,
                                          TextFilterIgnoreList.ignore_type, TextFilterIgnoreList.ignore)
                                   .filter_by(guild_id=guild_id, ignore_type="channel")).all()
            rows += session.execute(select(TextFilterIgnoreList.ignore_id, TextFilterIgnoreList.guild_id,
                                          TextFilterIgnoreList.ignore_type, TextFilterIgnoreList.ignore)
                                   .filter_by(guild_id=guild_id, ignore_type="user")).all()
            return rows

    def get_mod_channel(self, guild_id):
        """
        Gets specific mod channels given a guild id

        :param guild_id: Guild ID to retrieve mod channel from
        :return: list of mod channels
        """
        with session_manager() as session:
            rows = session.execute(select(TextFilterModeration.channel_id)
                                   .filter_by(guild_id=guild_id)).all()
            return rows

    def remove_mod_channel(self, guild_id, channel_id):
        """
        Removes a specific mod channel in a guild

        :param guild_id: Guild ID to remove mod channel from
        :param channel_id: Mod channel to be removed
        :return:
        """
        with session_manager() as session:
            session.execute(delete(TextFilterModeration)
                            .filter_by(guild_id=guild_id, channel_id=channel_id))
            session.commit()

    def does_word_exist(self, ft_id):
        """
        Checks if word exists in database given an ID

        :param ft_id: filtered text id of word to be removed
        :return boolean of whether the word exists or not:
        """
        with session_manager() as session:
            return len(session.execute(select(TextFilter)
                                       .filter_by(filtered_text_id=ft_id)).all()) > 0

    def does_ignore_exist(self, ignore_id):
        """
        Checks if ignore exists in database given an ID

        :param ignore_id: ignore id of ignore to be removed
        :return boolean of whether the ignore exists or not:
        """
        with session_manager() as session:
            return len(session.execute(select(TextFilterIgnoreList)
                                       .filter_by(ignore_id=ignore_id)).all()) > 0
