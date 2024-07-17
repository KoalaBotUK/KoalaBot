from enum import Enum

from dislord.types import ObjDict
from dislord.discord.interactions.application_commands.models import ApplicationCommandOptionChoice
from dislord.discord.interactions.components.models import Component
from dislord.discord.resources.channel.allowed_mentions import AllowedMentions
from dislord.discord.resources.channel.attachment import PartialAttachment
from dislord.discord.resources.channel.embed import Embed
from dislord.discord.resources.channel.message import MessageFlags
from dislord.discord.reference import Missing
from dislord.discord.resources.poll.poll import Poll


class ModalInteractionCallbackData(ObjDict):
    custom_id: str
    title: str
    components: list[Component]


class AutocompleteInteractionCallbackData(ObjDict):
    choices: list[ApplicationCommandOptionChoice]


class MessagesInteractionCallbackData(ObjDict):
    tts: bool | Missing
    content: str | Missing
    embeds: list[Embed] | Missing
    allowed_mentions: AllowedMentions | Missing
    flags: MessageFlags
    components: list[Component] | Missing
    attachments: list[PartialAttachment] | Missing
    poll: Poll | Missing


InteractionCallbackData = MessagesInteractionCallbackData | AutocompleteInteractionCallbackData | ModalInteractionCallbackData


class InteractionCallbackType(Enum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7  # Only valid for component-based receiving_and_responding
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9  # Not available for MODAL_SUBMIT and PING receiving_and_responding.
    PREMIUM_REQUIRED = 10  # Not available for APPLICATION_COMMAND_AUTOCOMPLETE and PING receiving_and_responding.


class InteractionResponse(ObjDict):
    type: InteractionCallbackType
    data: InteractionCallbackData | Missing

    @staticmethod
    def pong():
        return InteractionResponse(type=InteractionCallbackType.PONG)

    @staticmethod
    def message(**kwargs):
        cls = InteractionResponse(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                                  data=MessagesInteractionCallbackData(**kwargs))
        return cls
