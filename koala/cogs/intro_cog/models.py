from sqlalchemy import Column, Integer, String, ForeignKey, orm
from koala.models import mapper_registry
from koala.db import setup


@mapper_registry.mapped
class GuildWelcomeMessages:
    __tablename__ = 'GuildWelcomeMessages'
    guild_id = Column(Integer, primary_key=True)
    welcome_message = Column(String, nullable=True)

    def __repr__(self):
        return "<GuildWelcomeMessages(%s, %s)>" % \
               (self.guild_id, self.welcome_message)


setup()
