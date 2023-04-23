# Futures
# Built-in/Generic Imports
# Libs
from discord import ActivityType
from sqlalchemy import Column, TIMESTAMP, VARCHAR, INT, types

# Own modules
from koala.models import mapper_registry, BaseModel


# Constants

# Variables
class DiscordActivityType(types.TypeDecorator):
    """
    Uses discord.ActivityType for python, but INT for storing in db
    """

    impl = types.INT

    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.value if value is not None else None

    def process_literal_param(self, value, dialect):
        return value.value if value is not None else None

    def process_result_value(self, value, dialect):
        return ActivityType(value) if value is not None else None

    def copy(self, **kw):
        return DiscordActivityType()

    @property
    def python_type(self):
        return ActivityType


@mapper_registry.mapped
class ScheduledActivities(BaseModel):
    __tablename__ = 'ScheduledActivities'
    activity_id = Column(INT, primary_key=True, autoincrement=True)
    activity_type = Column(DiscordActivityType, comment="-1: unknown, 0: Playing, 1: Streaming, 2: Listening, "
                                                        "3: Watching, 4: Custom, 5: Competing")
    stream_url = Column(VARCHAR(100), nullable=True)
    message = Column(VARCHAR(100))
    time_start = Column(TIMESTAMP)
    time_end = Column(TIMESTAMP)

    def __repr__(self):
        return "<ScheduledActivities(%s, %s, %s)>" % \
               (self.activity_id, self.activity_type, self.message)
