from sqlalchemy import Column, INT, VARCHAR, ForeignKey, UniqueConstraint

from koala.db import setup
from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildRFRMessages:
    __tablename__ = 'GuildRFRMessages'
    guild_id = Column(DiscordSnowflake, ForeignKey("GuildExtensions.guild_id"))
    channel_id = Column(DiscordSnowflake)
    message_id = Column(DiscordSnowflake)
    emoji_role_id = Column(INT, primary_key=True)
    __table_args__ = (UniqueConstraint('guild_id', 'channel_id', 'message_id', name="uniq_message"),)

    def __repr__(self):
        return "<GuildRFRMessages(%s, %s, %s, %s)>" % \
               (self.emoji_role_id, self.guild_id, self.channel_id, self.message_id)

    def old_format(self):
        return int(self.guild_id), int(self.channel_id), int(self.message_id), int(self.emoji_role_id)


@mapper_registry.mapped
class RFRMessageEmojiRoles:
    __tablename__ = 'RFRMessageEmojiRoles'
    emoji_role_id = Column(INT, ForeignKey("GuildRFRMessages.emoji_role_id"), primary_key=True)
    emoji_raw = Column(VARCHAR(50), primary_key=True)
    role_id = Column(DiscordSnowflake, primary_key=True)
    __table_args__ = (UniqueConstraint('emoji_role_id', 'emoji_raw', name="uniq_emoji"),
                      UniqueConstraint('emoji_role_id', 'role_id', name="uniq_role_emoji"))

    def __repr__(self):
        return "<RFRMessageEmojiRoles(%s, %s, %s)>" % \
               (self.emoji_role_id, self.emoji_raw, self.role_id)


@mapper_registry.mapped
class GuildRFRRequiredRoles:
    __tablename__ = 'GuildRFRRequiredRoles'
    guild_id = Column(DiscordSnowflake, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column(DiscordSnowflake, primary_key=True)
    __table_args__ = (UniqueConstraint('guild_id', 'role_id', name="uniq_guild_role"),)

    def __repr__(self):
        return "<GuildRFRRequiredRoles(%s, %s)>" % \
               (self.guild_id, self.role_id)


setup()
