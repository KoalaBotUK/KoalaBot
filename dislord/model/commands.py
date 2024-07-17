from discord import Permissions

from dislord.discord.interactions.application_commands.enums import ApplicationCommandType
from dislord.discord.interactions.application_commands.models import ApplicationCommand as ApplicationCommandPayload, \
    ApplicationCommandOption
from dislord.discord.interactions.receiving_and_responding.interaction import InteractionContextType
from dislord.discord.reference import Snowflake, Missing, Locale
from dislord.discord.resources.application.enums import ApplicationIntegrationType
from dislord.model.base import BaseModel


class ApplicationCommand(ApplicationCommandPayload):

    @staticmethod
    def from_payload(payload: ApplicationCommandPayload) -> 'ApplicationCommand':
        return ApplicationCommand(
            **payload
        )

    def to_payload(self) -> ApplicationCommandPayload:
        return self

    def __eq__(self, other):
        eq_list = ['guild_id', 'name', 'description', 'type', 'name_localization', 'description_localizations',
                   'options', 'default_member_permissions', 'dm_permission', 'default_permission', 'nsfw']
        result = True
        for eq_attr in eq_list:
            self_attr = getattr(self, eq_attr, None)
            other_attr = getattr(other, eq_attr, None)
            result = result and (self_attr == other_attr or self_attr is other_attr) # compare_missing_none(self_attr, other_attr)
        return result

    def __post_init__(self):
        if self.guild_id is not None and self.guild_id is not Missing:
            self.dm_permission = None
