from sqlalchemy import Column, ForeignKey

from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class GuildColourChangePermissions:
    __tablename__ = 'GuildColourChangePermissions'
    guild_id = Column(DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True)
    role_id = Column(DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<GuildColourChangePermissions(%s, %s)>" % \
               (self.guild_id, self.role_id)


@mapper_registry.mapped
class GuildInvalidCustomColourRoles:
    __tablename__ = 'GuildInvalidCustomColourRoles'
    guild_id = Column(DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True)
    role_id = Column(DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<GuildColourChangePermissions(%s, %s)>" % \
               (self._guild_id, self._role_id)
