# Futures
# Built-in/Generic Imports
# Libs
from discord import ActivityType
from sqlalchemy import Column, TIMESTAMP, Enum, VARCHAR, INT

# Own modules
from koala.models import mapper_registry

# Constants

# Variables


@mapper_registry.mapped
class ScheduledActivities:
    __tablename__ = 'ScheduledActivities'
    activity_id = Column(INT, primary_key=True, autoincrement=True)
    activity_type = Column(Enum(ActivityType), comment="0: Playing, 1: Streaming, 2: Listening, 3: Watching, 4: Custom,"
                                                       " 5: Competing")
    stream_url = Column(VARCHAR(100), nullable=True)
    message = Column(VARCHAR(100))
    time_start = Column(TIMESTAMP)
    time_end = Column(TIMESTAMP)

    def __repr__(self):
        return "<ScheduledActivities(%s, %s, %s)>" % \
               (self.activity_id, self.activity_type, self.message)
