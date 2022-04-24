# Futures
# Built-in/Generic Imports
# Libs
from discord import ActivityType
from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum

# Own modules
from koala.models import mapper_registry, BaseModel
from koala.db import setup

# Constants

# Variables


@mapper_registry.mapped
class ScheduledActivities(BaseModel):
    __tablename__ = 'ScheduledActivities'
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_type = Column(Enum(ActivityType), comment="0: Playing, 1: Streaming, 2: Listening, 3: Watching, 4: Custom,"
                                                       " 5: Competing")
    stream_url = Column(String, nullable=True)
    message = Column(String)
    time_start = Column(TIMESTAMP)
    time_end = Column(TIMESTAMP)

    def __repr__(self):
        return "<ScheduledActivities(%s, %s, %s)>" % \
               (self.activity_id, self.activity_type, self.message)


setup()
