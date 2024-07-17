from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class OverwriteType(IntEnum):
    ROLE = 0
    MEMBER = 1


class Overwrite(ObjDict):
    id: Snowflake
    type: OverwriteType
    allow: str
    deny: str
