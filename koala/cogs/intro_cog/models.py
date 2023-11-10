from sqlalchemy import Column, VARCHAR

from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildWelcomeMessages:
    __tablename__ = 'GuildWelcomeMessages'
    guild_id = Column(DiscordSnowflake, primary_key=True)
    welcome_message = Column(VARCHAR(2000, collation="utf8mb4_unicode_520_ci"), nullable=True)

    def __repr__(self):
        return "<GuildWelcomeMessages(%s, %s)>" % \
               (self.guild_id, self.welcome_message)
