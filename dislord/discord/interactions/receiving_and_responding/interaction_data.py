from typing import Self

from dislord.types import ObjDict
from dislord.discord.interactions.application_commands.enums import ApplicationCommandOptionType
from dislord.discord.interactions.components.models import SelectOption, Component
from dislord.discord.topics.permissions.role import Role
from dislord.discord.resources.channel.attachment import Attachment
from dislord.discord.resources.channel.channel import PartialChannel
from dislord.discord.resources.channel.partial_message import PartialMessage
from dislord.discord.resources.guild.guild_member import PartialGuildMember
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Snowflake, Missing


class ApplicationCommandInteractionDataOption(ObjDict):
    name: str
    type: ApplicationCommandOptionType
    value: str | int | float | bool | Missing
    options: list[Self] | Missing
    focused: bool | Missing


class ModalSubmitData(ObjDict):
    custom_id: str
    components: list[Component]


class ResolvedData(ObjDict):
    users: dict[Snowflake, User] | Missing
    members: dict[Snowflake, PartialGuildMember] | Missing
    roles: dict[Snowflake, Role] | Missing
    channels: dict[Snowflake, PartialChannel] | Missing
    messages: dict[Snowflake, PartialMessage] | Missing
    attachments: dict[Snowflake, Attachment] | Missing


class MessageComponentData(ObjDict):
    custom_id: str
    component_type: int
    values: list[SelectOption] | Missing
    resolved: ResolvedData | Missing


class ApplicationCommandData(ObjDict):
    id: Snowflake
    name: str
    type: int
    resolved: ResolvedData | Missing
    options: list[ApplicationCommandInteractionDataOption] | Missing
    guild_id: Snowflake | Missing
    target: Snowflake | Missing


InteractionData = ApplicationCommandData | MessageComponentData | ModalSubmitData
