from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class FollowedChannel(ObjDict):
    channel_id: Snowflake
    webhook_id: Snowflake
