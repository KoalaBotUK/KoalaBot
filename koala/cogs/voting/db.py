#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports
from random import randint

# Libs
import discord
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

# Own modules
from koala.db import session_manager
from .log import logger
from .models import Votes, VoteTargetRoles, VoteOptions, VoteSent
from .option import Option
from .two_way import TwoWay
from .utils import MAX_ID_VALUE, MIN_ID_VALUE
from .vote import Vote


# Constants

# Variables


async def add_reactions(vote, msg):
    """
    Adds the relevant reactions from a vote to a given message
    :param vote: the vote the message is for
    :param msg: the discord.Message object to react on
    :return:
    """
    for x in range(len(vote.options)):
        await msg.add_reaction(VoteManager.emote_reference[x])


def create_embed(vote):
    """
    Creates an embed of the current vote configuration
    :return: discord.Embed
    """
    embed = discord.Embed(title=vote.title)
    for x, option in enumerate(vote.options):
        embed.add_field(name=f"{VoteManager.emote_reference[x]} - {option.head}", value=option.body, inline=False)
    return embed


async def get_results(bot, vote):
    """
    Gathers the results from all users who were sent the vote
    :param vote: the vote object
    :param bot: the discord.commands.Bot that sent out the vote messages
    :return: dict of results
    """
    results = {}
    for u_id, msg_id in vote.sent_to.items():
        user = bot.get_user(u_id)
        if user:
            msg = await user.fetch_message(msg_id)
            for reaction in msg.reactions:
                if reaction.count > 1:
                    opt = vote.options[VoteManager.emote_reference[reaction.emoji]]
                    if opt in results.keys():
                        results[opt] += 1
                    else:
                        results[opt] = 1
                    break
        else:
            logger.error("User %s not found for msg_id: %s" % (u_id, msg_id))
    return results


class VoteManager:
    def __init__(self):
        """
        Manages votes for the bot
        """
        self.configuring_votes = {}
        self.sent_votes = {}
        self.vote_lookup = {}

    emote_reference = TwoWay({0: "1️⃣", 1: "2️⃣", 2: "3️⃣",
                              3: "4️⃣", 4: "5️⃣", 5: "6️⃣",
                              6: "7️⃣", 7: "8️⃣", 8: "9️⃣", 9: "🔟"})

    def generate_unique_opt_id(self):
        with session_manager() as session:
            used_ids = session.execute(select(VoteOptions.opt_id)).all()
            return self.gen_id(len(used_ids) > (MAX_ID_VALUE - MIN_ID_VALUE))

    def gen_vote_id(self):
        return self.gen_id(len(self.configuring_votes.keys()) == (MAX_ID_VALUE - MIN_ID_VALUE))

    def gen_id(self, cond):
        if cond:
            return None
        while True:
            temp_id = randint(MIN_ID_VALUE, MAX_ID_VALUE)
            if temp_id not in self.configuring_votes.keys():
                return temp_id

    def load_from_db(self):
        with session_manager() as session:
            existing_votes = session.execute(select(Votes.vote_id, Votes.author_id, Votes.guild_id,
                                                    Votes.title, Votes.chair_id, Votes.voice_id, Votes.end_time)).all()
            for v_id, a_id, g_id, title, chair_id, voice_id, end_time in existing_votes:
                vote = Vote(v_id, title, a_id, g_id)
                vote.set_chair(chair_id)
                vote.set_vc(voice_id)
                self.vote_lookup[(a_id, title)] = v_id

                target_roles = session.execute(select(VoteTargetRoles.role_id).filter_by(vote_id=v_id)).all()
                if target_roles:
                    for r_id in target_roles:
                        vote.add_role(r_id[0])

                options = session.execute(select(VoteOptions.opt_id, VoteOptions.option_title,
                                                 VoteOptions.option_desc).filter_by(vote_id=v_id)).all()
                if options:
                    for o_id, o_title, o_desc in options:
                        vote.add_option(Option(o_title, o_desc, opt_id=o_id))

                delivered = session.execute(select(VoteSent.vote_receiver_id, VoteSent.vote_receiver_message)
                                            .filter_by(vote_id=v_id)).all()
                if delivered:
                    self.sent_votes[v_id] = vote
                    for rec_id, msg_id in delivered:
                        vote.register_sent(rec_id, msg_id)
                else:
                    self.configuring_votes[a_id] = vote

    def get_vote_from_id(self, v_id):
        """
        Returns a vote from a given discord context
        :param v_id: id of the vote
        :return: Relevant vote object
        """
        return self.sent_votes[v_id]

    def get_configuring_vote(self, author_id):
        return self.configuring_votes[author_id]

    def has_active_vote(self, author_id):
        """
        Checks if a user already has an active vote somewhere
        :param author_id: id of the author
        :return: True if they have an existing vote, otherwise False
        """
        return author_id in self.configuring_votes.keys()

    def create_vote(self, author_id, guild_id, title, session: Session):
        """
        Creates a vote object and assigns it to a users ID
        :param author_id: id of the author of the vote
        :param guild_id: id of the guild of the vote
        :param title: title of the vote
        :return: the newly created Vote object
        """
        with session_manager() as session:
            v_id = self.gen_vote_id()
            vote = Vote(v_id, title, author_id, guild_id)
            self.vote_lookup[(author_id, title)] = v_id
            self.configuring_votes[author_id] = vote
            session.add(Votes(vote_id=vote.id, author_id=author_id, guild_id=vote.guild, title=vote.title,
                              chair_id=vote.chair, voice_id=vote.target_voice_channel, end_time=vote.end_time))
            session.commit()
            return vote

    def cancel_sent_vote(self, v_id):
        """
        Removed a vote from the list of active votes
        :param v_id: the vote id
        :return: None
        """
        vote = self.sent_votes.pop(v_id)
        self.cancel_vote(vote)

    def cancel_configuring_vote(self, author_id):
        vote = self.configuring_votes.pop(author_id)
        self.cancel_vote(vote)

    def cancel_vote(self, vote):
        with session_manager() as session:
            self.vote_lookup.pop((vote.author, vote.title))
            session.execute(delete(Votes).filter_by(vote_id=vote.id))
            session.execute(delete(VoteTargetRoles).filter_by(vote_id=vote.id))
            session.execute(delete(VoteOptions).filter_by(vote_id=vote.id))
            session.execute(delete(VoteSent).filter_by(vote_id=vote.id))
            session.commit()

    def was_sent_to(self, msg_id):
        """
        Checks if a given message was sent by the bot for a vote, so it knows if it should listen for reactions on it.
        :param msg_id: the message that has been reacted on
        :return: the relevant vote for the message, if there is one
        """
        for vote in self.sent_votes.values():
            if msg_id in vote.sent_to.values():
                return vote
        return None


