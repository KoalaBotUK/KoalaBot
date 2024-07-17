from enum import IntFlag, IntEnum
from typing import Self

from dislord.types import ObjDict
from dislord.discord.interactions.components.models import Component
from dislord.discord.interactions.receiving_and_responding.interaction_data import ResolvedData
from dislord.discord.interactions.receiving_and_responding.message_interaction import MessageInteraction
from dislord.discord.resources.application.models import PartialApplication
from dislord.discord.resources.channel.channel import Channel
from dislord.discord.resources.channel.channel_mention import ChannelMention
from dislord.discord.resources.channel.message_interaction_metadata import MessageInteractionMetadata
from dislord.discord.resources.channel.message_reference import MessageReference
from dislord.discord.resources.channel.partial_message import PartialMessage
from dislord.discord.resources.channel.role_subscription_data import RoleSubscriptionData
from dislord.discord.resources.poll.poll import Poll
from dislord.discord.resources.sticker.sticker import Sticker
from dislord.discord.resources.sticker.sticker_item import StickerItem
from dislord.discord.reference import Missing, Snowflake


class MessageFlags(IntFlag):
    CROSSPOSTED = 1 << 0
    IS_CROSSPOST = 1 << 1
    SUPPRESS_EMBEDS = 1 << 2
    SOURCE_MESSAGE_DELETED = 1 << 3
    URGENT = 1 << 4
    HAS_THREAD = 1 << 5
    EPHEMERAL = 1 << 6
    LOADING = 1 << 7
    FAILED_TO_MENTION_SOME_ROLES_IN_THREAD = 1 << 8
    SUPPRESS_NOTIFICATIONS = 1 << 12
    IS_VOICE_MESSAGE = 1 << 13


class MessageActivityType(IntEnum):
    JOIN = 1
    SPECTATE = 2
    LISTEN = 3
    JOIN_REQUEST = 5


class MessageActivity(ObjDict):
    type: MessageActivityType
    party_id: str | Missing


class Message(PartialMessage):
    mention_channels: list[ChannelMention] | Missing
    nonce: int | str | Missing
    webhook_id: Snowflake | Missing
    activity: MessageActivity | Missing
    application: PartialApplication | Missing
    application_id: Snowflake | Missing
    message_reference: MessageReference | Missing
    flags: MessageFlags | Missing
    referenced_message: Self | Missing | None
    interaction_metadata: MessageInteractionMetadata | Missing
    interaction: MessageInteraction | Missing
    thread: Channel | Missing
    components: list[Component] | Missing
    sticker_items: list[StickerItem] | Missing
    stickers: list[Sticker] | Missing
    position: int | Missing
    role_subscription_data = RoleSubscriptionData | Missing
    resolved: ResolvedData | Missing
    poll: Poll | Missing
