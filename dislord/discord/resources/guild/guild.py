from enum import IntEnum, IntFlag, Flag

from dislord.types import ObjDict
from dislord.discord.topics.permissions.role import Role
from dislord.discord.resources.emoji.emoji import Emoji
from dislord.discord.resources.guild.welcome_screen import WelcomeScreen
from dislord.discord.resources.sticker.sticker import Sticker
from dislord.discord.reference import Missing, Snowflake, Locale


class MutableGuildFeatures(Flag):
    COMMUNITY = "COMMUNITY"
    DISCOVERABLE = "DISCOVERABLE"
    INVITES_DISABLED = "INVITES_DISABLED"
    RAID_ALERTS_DISABLED = "RAID_ALERTS_DISABLED"


class GuildFeatures(Flag):
    ANIMATED_BANNER = "ANIMATED_BANNER"
    ANIMATED_ICON = "ANIMATED_ICON"
    APPLICATION_COMMAND_PERMISSIONS_V2 = "APPLICATION_COMMAND_PERMISSIONS_V2"
    AUTO_MODERATION = "AUTO_MODERATION"
    BANNER = "BANNER"
    COMMUNITY = "COMMUNITY"
    CREATOR_MONETIZABLE_PROVISIONAL = "CREATOR_MONETIZABLE_PROVISIONAL"
    CREATOR_STORE_PAGE = "CREATOR_STORE_PAGE"
    DEVELOPER_SUPPORT_SERVER = "DEVELOPER_SUPPORT_SERVER"
    DISCOVERABLE = "DISCOVERABLE"
    FEATURABLE = "FEATURABLE"
    INVITES_DISABLED = "INVITES_DISABLED"
    INVITE_SPLASH = "INVITE_SPLASH"
    MEMBER_VERIFICATION_GATE_ENABLED = "MEMBER_VERIFICATION_GATE_ENABLED"
    MORE_STICKERS = "MORE_STICKERS"
    NEWS = "NEWS"
    PARTNERED = "PARTNERED"
    PREVIEW_ENABLED = "PREVIEW_ENABLED"
    RAID_ALERTS_DISABLED = "RAID_ALERTS_DISABLED"
    ROLE_ICONS = "ROLE_ICONS"
    ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE = "ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE"
    ROLE_SUBSCRIPTIONS_ENABLED = "ROLE_SUBSCRIPTIONS_ENABLED"
    TICKETED_EVENTS_ENABLED = "TICKETED_EVENTS_ENABLED"
    VANITY_URL = "VANITY_URL"
    VERIFIED = "VERIFIED"
    VIP_REGIONS = "VIP_REGIONS"
    WELCOME_SCREEN_ENABLED = "WELCOME_SCREEN_ENABLED"


class SystemChannelFlags(IntFlag):
    SUPPRESS_JOIN_NOTIFICATIONS = 1 << 0
    SUPPRESS_PREMIUM_SUBSCRIPTIONS = 1 << 1
    SUPPRESS_GUILD_REMINDER_NOTIFICATIONS = 1 << 2
    SUPPRESS_JOIN_NOTIFICATION_REPLIES = 1 << 3
    SUPPRESS_ROLE_SUBSCRIPTION_PURCHASE_NOTIFICATIONS = 1 << 4
    SUPPRESS_ROLE_SUBSCRIPTION_PURCHASE_NOTIFICATION_REPLIES = 1 << 5


class PremiumTier(IntEnum):
    NONE = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class GuildNsfwLevel(IntEnum):
    DEFAULT = 0
    EXPLICIT = 1
    SAFE = 2
    AGE_RESTRICTED = 3


class VerificationLevel(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class MfaLevel(IntEnum):
    NONE = 0
    ELEVATED = 1


class ExplicitContentFilterLevel(IntEnum):
    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2


class DefaultMessageNotificationLevel(IntEnum):
    ALL_MESSAGES = 0
    ONLY_MENTIONS = 1


class PartialGuild(ObjDict):
    id: Snowflake
    name: str
    description: str | None
    region: str | Missing
    afk_channel_id: Snowflake | None
    system_channel_id: Snowflake | None
    icon_hash: str | Missing | None


class Guild(PartialGuild):
    icon: str | None
    splash: str | None
    discovery_splash: str | None
    owner: bool | Missing
    owner_id: Snowflake
    permissions: str | Missing
    afk_timeout: int
    widget_enabled: bool | Missing
    widget_channel_id: Snowflake | Missing | None
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotificationLevel
    explicit_content_filter: ExplicitContentFilterLevel
    roles: list[Role]
    emojis: list[Emoji]
    features: list[GuildFeatures]
    mfa_level: MfaLevel
    application_id: Snowflake | None
    system_channel_flags: SystemChannelFlags
    rules_channel_id: Snowflake | None
    max_presences: int | Missing | None
    max_members: int | Missing
    vanity_url_code: str | None
    banner: str | None
    premium_tier: PremiumTier
    premium_subscription_count: int | Missing
    preferred_locale: Locale
    public_updates_channel_id: Snowflake | None
    max_video_channel_users: int | Missing
    max_stage_video_channel_users: int | Missing
    approximate_member_count: int | Missing
    approximate_presence_count: int | Missing
    welcome_screen: WelcomeScreen | Missing
    nsfw_level: GuildNsfwLevel
    stickers: list[Sticker] | Missing
    premium_progress_bar_enabled: bool
    safety_alerts_channel_id: Snowflake | None
