from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from koala.db import setup
from koala.models import mapper_registry


@mapper_registry.mapped
class GuildRFRMessages:
    __tablename__ = 'GuildRFRMessages'
    guild_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"))
    channel_id = Column(Integer)
    message_id = Column(Integer)
    emoji_role_id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint('guild_id', 'channel_id', 'message_id'),)

    def __repr__(self):
        return "<GuildRFRMessages(%s, %s, %s, %s)>" % \
               (self.emoji_role_id, self.guild_id, self.channel_id, self.message_id)

    def old_format(self):
        return self.guild_id, self.channel_id, self.message_id, self.emoji_role_id


@mapper_registry.mapped
class RFRMessageEmojiRoles:
    __tablename__ = 'RFRMessageEmojiRoles'
    emoji_role_id = Column(Integer, ForeignKey("GuildRFRMessages.emoji_role_id"), primary_key=True)
    emoji_raw = Column(String, primary_key=True)
    role_id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint('emoji_role_id', 'emoji_raw'),
                      UniqueConstraint('emoji_role_id', 'role_id'))

    def __repr__(self):
        return "<RFRMessageEmojiRoles(%s, %s, %s)>" % \
               (self.emoji_role_id, self.emoji_raw, self.role_id)


@mapper_registry.mapped
class GuildRFRRequiredRoles:
    __tablename__ = 'GuildRFRRequiredRoles'
    guild_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint('guild_id', 'role_id'),)

    def __repr__(self):
        return "<GuildRFRRequiredRoles(%s, %s)>" % \
               (self.guild_id, self.role_id)


setup()
