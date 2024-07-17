from dislord.types import ObjDict
from dislord.discord.reference import Snowflake
from dislord.types import ObjDict


class DefaultReaction(ObjDict):
    emoji_id: Snowflake | None
    emoji_name: str | None
