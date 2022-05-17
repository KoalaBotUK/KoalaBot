from sqlalchemy import Column, INT, ForeignKey

from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildUsage:
    __tablename__ = 'GuildUsage'
    guild_id = Column(DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True)
    last_message_epoch_time = Column(INT)

    def __repr__(self):
        return "<GuildUsage(%s, %s)>" % \
               (self.guild_id, self.last_message_epoch_time)
