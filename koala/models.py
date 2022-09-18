# Futures
# Built-in/Generic Imports
# Libs
import sqlalchemy.dialects.mssql.information_schema
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import registry

# Own modules

# Constants

# Variables

mapper_registry = registry()


class BaseModel:
    """
    The base, serializable model for all sqlalchemy models in this project
    """
    __table__: sqlalchemy.dialects.mssql.information_schema.tables

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@mapper_registry.mapped
class KoalaExtensions:
    __tablename__ = 'KoalaExtensions'
    extension_id = Column(String, primary_key=True)
    subscription_required = Column(Integer)
    available = Column(Boolean)
    enabled = Column(Boolean)

    def __repr__(self):
        return "KoalaExtensions(%s, %s, %s, %s)>" % \
               (self.extension_id, self.subscription_required, self.available, self.enabled)


@mapper_registry.mapped
class GuildExtensions:
    __tablename__ = 'GuildExtensions'
    extension_id = Column(String, ForeignKey("KoalaExtensions.extension_id"), primary_key=True)
    guild_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return "GuildExtensions(%s, %s)>" % \
               (self.extension_id, self.guild_id)

@mapper_registry.mapped
class AdminRoles:
    __tablename__ = 'AdminRoles'
    guild_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return "AdminRoles(%s, %s)" % \
               (self.guild_id, self.guild_id)
