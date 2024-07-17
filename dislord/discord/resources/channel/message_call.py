from dislord.types import ObjDict
from dislord.discord.reference import Snowflake, ISOTimestamp, Missing


class MessageCall(ObjDict):
    participants: list[Snowflake]
    ended_timestamp: ISOTimestamp | Missing | None
