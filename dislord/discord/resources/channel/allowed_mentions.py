from enum import StrEnum

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class AllowedMentionType(StrEnum):
    ROLES = "roles"
    USERS = "users"
    EVERYONE = "everyone"


class AllowedMentions(ObjDict):
    parse: list[AllowedMentionType]
    role: list[Snowflake]
    users: list[Snowflake]
    replied_user: bool
