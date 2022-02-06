from sqlalchemy import Column, Integer, ForeignKey
from koala.models import mapper_registry


@mapper_registry.mapped
class GuildColourChangePermissions:
    __tablename__ = 'GuildColourChangePermissions'
    guild_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return "GuildColourChangePermissions(%s, %s)>" % \
               (self.guild_id, self.role_id)


@mapper_registry.mapped
class GuildInvalidCustomColourRoles:
    __tablename__ = 'GuildInvalidCustomColourRoles'
    guild_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    role_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return "GuildColourChangePermissions(%s, %s)>" % \
               (self.guild_id, self.role_id)
