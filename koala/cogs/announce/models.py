from sqlalchemy import Column, INT, ForeignKey

from koala.db import setup
from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildUsage:
    __tablename__ = 'GuildUsage'
    guild_id = Column(DiscordSnowflake, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    last_message_epoch_time = Column(INT)

    def __repr__(self):
        return "<GuildUsage(%s, %s)>" % \
               (self.guild_id, self.last_message_epoch_time)


setup()
