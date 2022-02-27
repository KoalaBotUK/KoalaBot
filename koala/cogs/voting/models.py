from sqlalchemy import Column, VARCHAR, FLOAT
from koala.models import mapper_registry, DiscordSnowflake
from koala.db import setup

# FIXME: Previous approach had no primary keys, this sets all as primary key but shouldn't affect existing databases
# FIXME: When refactoring database, set a primary key


@mapper_registry.mapped
class Votes:
    __tablename__ = 'Votes'
    vote_id = Column(DiscordSnowflake, primary_key=True)
    author_id = Column(DiscordSnowflake, primary_key=True)
    guild_id = Column(DiscordSnowflake, primary_key=True)
    title = Column(VARCHAR(200), primary_key=True)
    chair_id = Column(DiscordSnowflake, nullable=True, primary_key=True)
    voice_id = Column(DiscordSnowflake, nullable=True, primary_key=True)
    end_time = Column(FLOAT, nullable=True, primary_key=True)

    def __repr__(self):
        return "<Votes(%s, %s, %s, %s, %s, %s, %s)>" % \
               (self.vote_id, self.author_id, self.guild_id, self.title, self.chair_id, self.voice_id, self.end_time)


@mapper_registry.mapped
class VoteTargetRoles:
    __tablename__ = 'VoteTargetRoles'
    vote_id = Column(DiscordSnowflake, primary_key=True)
    role_id = Column(DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<VoteTargetRoles(%s, %s)>" % \
               (self.vote_id, self.role_id)


@mapper_registry.mapped
class VoteOptions:
    __tablename__ = 'VoteOptions'
    vote_id = Column(DiscordSnowflake, primary_key=True)
    opt_id = Column(DiscordSnowflake, primary_key=True)
    option_title = Column(VARCHAR(150), primary_key=True)
    option_desc = Column(VARCHAR(150), primary_key=True)

    def __repr__(self):
        return "<VoteOptions(%s, %s, %s, %s)>" % \
               (self.vote_id, self.opt_id, self.option_title, self.option_desc)


@mapper_registry.mapped
class VoteSent:
    __tablename__ = 'VoteSent'
    vote_id = Column(DiscordSnowflake, primary_key=True)
    vote_receiver_id = Column(DiscordSnowflake, primary_key=True)
    vote_receiver_message = Column(DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<VoteSent(%s, %s, %s)>" % \
               (self.vote_id, self.vote_receiver_id, self.vote_receiver_message)


setup()
