from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class ForumTag(ObjDict):
    id: Snowflake
    name: str
    moderated: bool
    emoji_id: Snowflake | None
    emoji_name: str | None
