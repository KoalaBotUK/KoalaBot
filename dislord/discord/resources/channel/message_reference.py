from dislord.types import ObjDict
from dislord.discord.reference import Snowflake, Missing


class MessageReference(ObjDict):
    message_id: Snowflake | Missing
    channel_id: Snowflake | Missing
    guild_id: Snowflake | Missing
    fail_if_not_exists: bool | Missing
