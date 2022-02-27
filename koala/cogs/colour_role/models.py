from sqlalchemy import Column, ForeignKey
from koala.db import setup
from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildColourChangePermissions:
    __tablename__ = 'GuildColourChangePermissions'
    guild_id = Column("guild_id", DiscordSnowflake, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column("role_id", DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<GuildColourChangePermissions(%s, %s)>" % \
               (self._guild_id, self._role_id)


@mapper_registry.mapped
class GuildInvalidCustomColourRoles:
    __tablename__ = 'GuildInvalidCustomColourRoles'
    guild_id = Column("guild_id", DiscordSnowflake, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column("role_id", DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<GuildColourChangePermissions(%s, %s)>" % \
               (self._guild_id, self._role_id)


setup()
