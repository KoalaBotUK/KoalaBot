from enum import IntFlag, IntEnum

from dislord.types import ObjDict
from dislord.discord.resources.channel.default_reaction import DefaultReaction
from dislord.discord.resources.channel.forum_tag import ForumTag
from dislord.discord.resources.channel.overwrite import Overwrite
from dislord.discord.resources.channel.thread_member import ThreadMember
from dislord.discord.resources.channel.thread_metadata import ThreadMetadata
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Missing, Snowflake, ISOTimestamp


class ForumLayoutType(IntEnum):
    NOT_SET = 0
    LIST_VIEW = 1
    GALLERY_VIEW = 2


class SortOrderType(IntEnum):
    LATEST_ACTIVITY = 0
    CREATION_DATE = 1


class ChannelFlags(IntFlag):
    PINNED = 1 << 1
    REQUIRE_TAG = 1 << 4
    HIDE_MEDIA_DOWNLOAD_OPTIONS = 1 << 15


class VideoQualityMode(IntEnum):
    AUTO = 1
    FULL = 2


class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_ANNOUNCEMENT = 5
    ANNOUNCEMENT_THREAD = 10
    PUBLIC_THREAD = 11
    PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13
    GUILD_DIRECTORY = 14
    GUILD_FORUM = 15
    GUILD_MEDIA = 16


class PartialChannel(ObjDict):
    id: Snowflake
    type: ChannelType
    name: str | Missing | None
    permissions: str | Missing
    thread_metadata: ThreadMetadata | Missing
    parent_id: Snowflake | Missing | None


class Channel(PartialChannel):
    guild_id: Snowflake | Missing
    position: int | Missing
    permission_overwrites: list[Overwrite] | Missing
    topic: str | Missing | None
    nsfw: bool | Missing
    last_message_id: Snowflake | Missing | None
    bitrate: int | Missing
    user_limit: int | Missing
    rate_limit_per_user: int | Missing
    recipients: list[User] | Missing
    icon: str | Missing | None
    owner_id: Snowflake | Missing
    application_id: Snowflake | Missing
    managed: bool | Missing
    last_pin_timestamp: ISOTimestamp | Missing | None
    rtc_region: str | Missing | None
    video_quality_mode: int | Missing
    message_count: int | Missing
    member_count: int | Missing
    member: ThreadMember | Missing
    default_auto_archive_duration: int | Missing
    flags: ChannelFlags | Missing
    total_message_sent: int | Missing
    available_tags: list[ForumTag] | Missing
    applied_tags: list[Snowflake] | Missing
    default_reaction_emoji: DefaultReaction | Missing | None
    default_thread_rate_limit_per_user: int | Missing
    default_sort_order: int | Missing | None
    default_forum_layout: int | Missing
