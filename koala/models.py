# Futures
# Built-in/Generic Imports
# Libs
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Own modules

# Constants
# Variables
Base = declarative_base()


class KoalaExtensions(Base):
    __tablename__ = 'KoalaExtensions'
    extension_id = Column(String, primary_key=True)
    subscription_required = Column(Integer)
    available = Column(Boolean)
    enabled = Column(Boolean)


class GuildExtensions(Base):
    __tablename__ = 'GuildExtensions'
    extension_id = Column(String, ForeignKey("KoalaExtensions.extension_id"), primary_key=True)
    guild_id = Column(Integer, primary_key=True)


class GuildWelcomeMessages(Base):
    __tablename__ = 'GuildWelcomeMessages'
    guild_id = Column(Integer, primary_key=True)
    welcome_message = Column(String, nullable=True)



