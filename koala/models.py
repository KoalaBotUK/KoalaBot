# Futures
# Built-in/Generic Imports
# Libs

import sqlalchemy.dialects.mssql.information_schema
import sqlalchemy.types as types
from sqlalchemy import Column, ForeignKey
from sqlalchemy import INT, VARCHAR, BOOLEAN
from sqlalchemy.orm import registry
from sqlalchemy.orm import validates

# Own modules

# Constants

# Variables

mapper_registry = registry()


class DiscordSnowflake(types.TypeDecorator):
    """
    Uses int for python, but VARCHAR(20) for storing in db
    """

    impl = types.VARCHAR(20)

    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value else None

    def process_literal_param(self, value, dialect):
        return str(value) if value else None

    def process_result_value(self, value, dialect):
        return int(value) if value else None

    def copy(self, **kw):
        return DiscordSnowflake(self.impl.length)

    @property
    def python_type(self):
        return int


class BaseModel:
    """
    The base, serializable model for all sqlalchemy models in this project
    """
    __table__: sqlalchemy.dialects.mssql.information_schema.tables

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@mapper_registry.mapped
class Guilds:
    __tablename__ = 'Guilds'
    guild_id = Column(DiscordSnowflake, primary_key=True)
    subscription = Column(INT)

    def __repr__(self):
        return "<Guilds(%s, %s)>" % \
               (self.guild_id, self.subscription)


@mapper_registry.mapped
class KoalaExtensions:
    __tablename__ = 'KoalaExtensions'
    extension_id = Column(VARCHAR(20), primary_key=True)
    subscription_required = Column(INT)
    available = Column(BOOLEAN)
    enabled = Column(BOOLEAN)

    def __repr__(self):
        return "<KoalaExtensions(%s, %s, %s, %s)>" % \
               (self.extension_id, self.subscription_required, self.available, self.enabled)


@mapper_registry.mapped
class GuildExtensions:
    __tablename__ = 'GuildExtensions'
    extension_id = Column(VARCHAR(20), ForeignKey("KoalaExtensions.extension_id", ondelete='CASCADE'), primary_key=True)
    guild_id = Column(DiscordSnowflake, primary_key=True)

    @validates("guild_id")
    def validate_discord_snowflake(self, key, guild_id):
        return int(guild_id)

    def __repr__(self):
        return "<GuildExtensions(%s, %s)>" % \
               (self.extension_id, self.guild_id)

