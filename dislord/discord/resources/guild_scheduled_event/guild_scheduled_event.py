from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Snowflake, Missing, ISOTimestamp


class GuildScheduledEventEntityMetadata(ObjDict):
    location: str | Missing


class GuildScheduledEventStatus(IntEnum):
    SCHEDULED = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELED = 4


class GuildScheduledEventEntityType(IntEnum):
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3


class GuildScheduledEventPrivacyLevel(IntEnum):
    GUILD_ONLY = 2


class GuildScheduledEvent(ObjDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake | None
    creator_id: Snowflake | Missing | None
    name: str
    description: str | Missing | None
    scheduled_start_time: ISOTimestamp
    scheduled_ent_time: ISOTimestamp | None
    privacy_level: GuildScheduledEventPrivacyLevel
    status: GuildScheduledEventStatus
    entity_type: GuildScheduledEventEntityType
    entity_id: Snowflake | None
    entity_metadata: GuildScheduledEventEntityMetadata | None
    creator: User | Missing
    user_count: int | Missing
    image: str | Missing | None
