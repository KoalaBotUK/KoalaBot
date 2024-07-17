from enum import IntFlag

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake, Missing


class RoleTags(ObjDict):
    bot_id: Snowflake | Missing
    integration_id: Snowflake | Missing
    premium_subscriber: Missing | None
    subscription_listing_id: Snowflake | Missing
    available_for_purchase: Missing | None
    guild_connections: Missing | None


class RoleFlags(IntFlag):
    IN_PROMPT = 1 << 0


class Role(ObjDict):
    id: Snowflake
    name: str
    color: int
    hoist: bool
    icon: str | Missing | None
    unicode_emoji: str | Missing | None
    position: int
    permissions: str
    managed: bool
    mentionable: bool
    tags: RoleTags | Missing
    flags: RoleFlags
