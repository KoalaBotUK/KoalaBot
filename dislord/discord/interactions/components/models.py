from dislord.types import ObjDict
from dislord.discord.interactions.components.enums import ButtonStyle, TextInputStyle, ComponentType
from dislord.discord.resources.channel.channel import ChannelType
from dislord.discord.reference import Snowflake, Missing
from dislord.discord.resources.emoji.emoji import PartialEmoji


class TextInput(ObjDict):
    type: ComponentType = ComponentType.TEXT_INPUT
    custom_id: str
    style: TextInputStyle
    label: str
    min_length: int | Missing
    max_length: int | Missing
    required: bool | Missing
    value: str | Missing
    placeholder: str | Missing


class SelectDefaultValue(ObjDict):
    id: Snowflake
    type: str


class SelectOption(ObjDict):
    label: str
    value: str
    description: str | Missing
    # emoji: PartialEmoji | Missing FIXME
    default: bool | Missing


class SelectMenu(ObjDict):
    type: ComponentType
    custom_id: str
    options: list[SelectOption] | Missing
    channel_types: list[ChannelType] | Missing
    placeholder: str | Missing
    default_values: list[SelectDefaultValue] | Missing
    min_values: int | Missing
    max_values: int | Missing
    disabled: bool | Missing


class Button(ObjDict):
    type: ComponentType = ComponentType.BUTTON
    style: ButtonStyle
    label: str | None
    emoji: PartialEmoji | Missing
    custom_id: str | Missing
    url: str | Missing
    disabled: bool | Missing


class ActionRow(ObjDict):
    type: ComponentType = ComponentType.ACTION_ROW
    components: list[Button | SelectMenu | TextInput]


Component = ActionRow | Button | SelectMenu | TextInput
