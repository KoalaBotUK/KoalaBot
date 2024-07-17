from dislord.types import ObjDict
from dislord.discord.resources.application_role_connection_metadata.enums import ApplicationRoleConnectionMetadataType
from dislord.discord.reference import Missing, Locale


class ApplicationRoleConnectionMetadata(ObjDict):
    type: ApplicationRoleConnectionMetadataType
    key: str
    name: str
    name_localizations: dict[Locale, str] | Missing | None
    description: str
    description_localizations: dict[Locale, str] | Missing | None