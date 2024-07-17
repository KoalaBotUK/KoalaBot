from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class PrivacyLevel(IntEnum):
    PUBLIC = 1
    GUILD_ONLY = 2


class StageInstance(ObjDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake
    topic: str
    privacy_level: PrivacyLevel
