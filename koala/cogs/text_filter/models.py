from sqlalchemy import Column, Integer, String, Boolean

from koala.db import setup
from koala.models import mapper_registry


@mapper_registry.mapped
class TextFilter:
    __tablename__ = 'TextFilter'
    filtered_text_id = Column(String, primary_key=True)
    guild_id = Column(Integer)
    filtered_text = Column(String)
    filter_type = Column(String)
    is_regex = Column(Boolean)

    def __repr__(self):
        return "<TextFilter(%s, %s, %s, %s, %s)>" % \
               (self.filtered_text_id, self.guild_id, self.filtered_text, self.filter_type, self.is_regex)


@mapper_registry.mapped
class TextFilterModeration:
    __tablename__ = 'TextFilterModeration'
    channel_id = Column(Integer, primary_key=True)
    guild_id = Column(Integer)

    def __repr__(self):
        return "<TextFilterModeration(%s, %s)>" % \
               (self.channel_id, self.guild_id)


@mapper_registry.mapped
class TextFilterIgnoreList:
    __tablename__ = 'TextFilterIgnoreList'
    ignore_id = Column(String, primary_key=True)
    guild_id = Column(Integer)
    ignore_type = Column(String)
    ignore = Column(Integer)

    def __repr__(self):
        return "<TextFilterIgnoreList(%s, %s, %s, %s)>" % \
               (self.ignore_id, self.guild_id, self.ignore_type, self.ignore)


setup()
