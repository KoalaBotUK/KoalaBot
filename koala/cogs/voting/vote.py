#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports

# Libs
from sqlalchemy import select, delete, update

# Own modules
from koala.db import session_manager
from .models import Votes, VoteTargetRoles, VoteSent, VoteOptions


# Constants

# Variables


class Vote:
    def __init__(self, v_id, title, author_id, guild_id):
        """
        An object containing methods and attributes of an active vote
        :param title: title of the vote
        :param author_id: creator of the vote
        :param guild_id: location of the vote
        """
        self.guild = guild_id
        self.id = v_id
        self.author = author_id
        self.title = title

        self.target_roles = []
        self.chair = None
        self.target_voice_channel = None
        self.end_time = None

        self.options = []

        self.sent_to = {}

    def is_ready(self):
        """
        Check if the vote is ready to be sent out
        :return: True if ready, False otherwise
        """
        return 1 < len(self.options) < 11 and not self.sent_to

    def add_role(self, role_id):
        """
        Adds a target role to send the vote to
        :param role_id: target role
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            self.target_roles.append(role_id)
            in_db = session.execute(select(VoteTargetRoles).filter_by(vote_id=self.id, role_id=role_id)).all()
            if not in_db:
                session.add(VoteTargetRoles(vote_id=self.id, role_id=role_id))
                session.commit()

    def remove_role(self, role_id):
        """
        Removes target role from vote targets
        :param role_id: target role
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            self.target_roles.remove(role_id)
            session.execute(delete(VoteTargetRoles).filter_by(vote_id=self.id, role_id=role_id))
            session.commit()

    def set_end_time(self, time=None):
        """
        Sets the end time of the vote.
        :param time: time in unix time
        :return:
        """
        with session_manager() as session:
            self.end_time = time
            session.execute(update(Votes).filter_by(vote_id=self.id).values(end_time=time))
            session.commit()

    def set_chair(self, chair_id=None):
        """
        Sets the chair of the vote to the given id
        :param chair_id: target chair
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            self.chair = chair_id
            vote: Votes = session.execute(select(Votes).filter_by(vote_id=self.id)).scalar()
            vote.chair_id = chair_id
            session.commit()

    def set_vc(self, channel_id=None):
        """
        Sets the target voice channel to a given channel id
        :param channel_id: target discord voice channel id
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            self.target_voice_channel = channel_id
            session.execute(update(Votes).filter_by(vote_id=self.id).values(voice_id=channel_id))
            session.commit()

    def add_option(self, option):
        """
        Adds an option to the vote
        :param option: Option object
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            self.options.append(option)
            in_db = session.execute(select(VoteOptions).filter_by(opt_id=option.id)).all()
            if not in_db:
                session.add(VoteOptions(vote_id=self.id, opt_id=option.id, option_title=option.head, option_desc=option.body))
                session.commit()

    def remove_option(self, index):
        """
        Removes an option from the vote
        :param index: the location in the list of options to remove
        :return: None
        """
        with session_manager() as session:
            if self.sent_to:
                return
            opt = self.options.pop(index-1)
            session.execute(delete(VoteOptions).filter_by(vote_id=self.id, opt_id=opt.id))
            session.commit()

    def register_sent(self, user_id, msg_id):
        """
        Marks a user as having been sent a message to vote on
        :param user_id: user who was sent the message
        :param msg_id: the id of the message that was sent
        :return:
        """
        with session_manager() as session:
            self.sent_to[user_id] = msg_id
            in_db = session.execute(select(VoteSent).filter_by(vote_receiver_message=msg_id)).all()
            if not in_db:
                session.add(VoteSent(vote_id=self.id, vote_receiver_id=user_id, vote_receiver_message=msg_id))
                session.commit()
