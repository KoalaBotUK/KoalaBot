from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from KoalaBot import DATABASE_PATH, DB_KEY
from utils.KoalaDBManager import ENCRYPTED_DB
import os
import logging

if os.name == 'nt' or not ENCRYPTED_DB:
    protocol = "sqlite:///"
else:
    protocol = "sqlite+pysqlcipher://:x'"+DB_KEY+"'@/"


Base = declarative_base()
connection_url = protocol+DATABASE_PATH
logging.error("connection_url"+connection_url)
print("connection_url"+connection_url)

engine = create_engine(connection_url, future=True, echo=True)
Session = sessionmaker(future=True)
Session.configure(bind=engine)
session = Session()


class KoalaExtensions(Base):
    __tablename__ = 'KoalaExtensions'
    __table_args__ = {'extend_existing': True}
    extension_id = Column(String, primary_key=True)
    subscription_required = Column(Integer)
    available = Column(Boolean)
    enabled = Column(Boolean)


class GuildExtensions(Base):
    __tablename__ = 'GuildExtensions'
    __table_args__ = {'extend_existing': True}
    extension_id = Column(String, ForeignKey("KoalaExtensions.extension_id"), primary_key=True)
    guild_id = Column(Integer)
