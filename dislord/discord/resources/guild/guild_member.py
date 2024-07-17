from enum import IntFlag

from dislord.types import ObjDict
from dislord.discord.resources.user.avatar_decoration_data import AvatarDecorationData
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Missing, Snowflake, ISOTimestamp


class GuildMemberFlags(IntFlag):
    DID_REJOIN = 1 << 0
    COMPLETED_ONBOARDING = 1 << 1
    BYPASSES_VERIFICATION = 1 << 2
    STARTED_ONBOARDING = 1 << 3


class PartialGuildMember(ObjDict):
    nick: str | Missing | None
    avatar: str | Missing | None
    roles: list[Snowflake]
    joined_at: ISOTimestamp
    premium_since: ISOTimestamp | Missing | None
    flags: GuildMemberFlags
    pending: bool | Missing
    permissions: str | Missing
    communication_disabled_until: ISOTimestamp | Missing | None
    avatar_decoration_data: AvatarDecorationData | Missing | None


class GuildMember(PartialGuildMember):
    user: User | Missing
    deaf: bool
    mute: bool
