from typing import Self, TypedDict

from discord import Permissions

from dislord.discord.interactions.application_commands.enums import ApplicationCommandType, \
    ApplicationCommandPermissionType, ApplicationCommandOptionType
from dislord.discord.interactions.receiving_and_responding.interaction import InteractionContextType
from dislord.discord.resources.application.enums import ApplicationIntegrationType
from dislord.discord.resources.channel.channel import ChannelType
from dislord.discord.reference import Snowflake, Missing, Locale
from dislord.types import ObjDict


class ApplicationCommandPermissions(ObjDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class GuildApplicationCommandPermissions(ObjDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    permissions: list[ApplicationCommandPermissions]


ApplicationCommandPermissionsObject = GuildApplicationCommandPermissions


class ApplicationCommandOptionChoice(ObjDict):
    name: str
    name_localizations: dict[Locale, str] | Missing | None
    value: str | int | float


class ApplicationCommandOption(ObjDict):
    type: ApplicationCommandOptionType
    name: str
    name_localizations: dict[Locale, str] | Missing | None
    description: str
    description_localizations: dict[Locale, str] | Missing | None
    required: bool | Missing
    choices: list[ApplicationCommandOptionChoice] | Missing
    options: list['ApplicationCommandOption'] | Missing
    channel_types: list[ChannelType] | Missing
    min_value: int | float | Missing
    max_values: int | float | Missing
    min_length: int | Missing
    max_length: int | Missing
    autocomplete: bool | Missing


class ApplicationCommand(ObjDict):
    id: Snowflake
    type: ApplicationCommandType | Missing
    application_id: Snowflake
    guild_id: Snowflake | Missing
    name: str
    name_localizations: dict[Locale, str] | Missing| None
    description: str
    description_localizations: dict[Locale, str] | Missing | None
    options: list[ApplicationCommandOption] | Missing
    default_member_permissions: Permissions | None
    dm_permission: bool | Missing   # Deprecated
    default_permission: bool | Missing | None = True
    nsfw: bool | Missing = False
    integration_types: list[ApplicationIntegrationType] | Missing = [ApplicationIntegrationType.GUILD_INSTALL]
    contexts: list[InteractionContextType] | Missing | None
    version: Snowflake