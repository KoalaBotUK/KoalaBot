from enum import IntEnum, IntFlag

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake, Missing, Locale


class PremiumType(IntEnum):
    NONE = 0
    NITRO_CLASSIC = 1
    NITRO = 2
    NITRO_BASIC = 3


class UserFlags(IntFlag):
    STAFF = 1 << 0
    PARTNER = 1 << 1
    HYPESQUAD = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    HYPESQUAD_ONLINE_HOUSE_1 = 1 << 6
    HYPESQUAD_ONLINE_HOUSE_2 = 1 << 7
    HYPESQUAD_ONLINE_HOUSE_3 = 1 << 8
    PREMIUM_EARLY_SUPPORTER = 1 << 9
    TEAM_PSEUDO_USER = 1 << 10
    BUG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT = 1 << 16
    VERIFIED_DEVELOPER = 1 << 17
    CERTIFIED_MODERATOR = 1 << 18
    BOT_HTTP_INTERACTIONS = 1 << 19
    ACTIVE_DEVELOPER = 1 << 22


class PartialUser(ObjDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: str | None


class User(PartialUser):
    global_name: str | None
    bot: bool | Missing
    system: bool | Missing
    mfa_enabled: bool | Missing
    banner: str | Missing | None
    accent_color: int | Missing | None
    locale: Locale | Missing
    verified: bool | Missing
    email: str | Missing | None
    flags: UserFlags | Missing
    premium_type: PremiumType | Missing
    public_flags: UserFlags | Missing
    avatar_decoration: str | Missing | None
