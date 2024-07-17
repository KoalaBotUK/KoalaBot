from dislord.discord.resources.guild.guild import PartialGuild
from dislord.discord.resources.user.user import User
from dislord.types import ObjDict
from dislord.discord.resources.application.enums import ApplicationIntegrationType
from dislord.discord.resources.application.flags import ApplicationFlags
from dislord.discord.reference import Snowflake, Missing


class InstallParams(ObjDict):
    scopes: list[str]
    permissions: str


class ApplicationIntegrationTypeConfiguration(ObjDict):
    oauth2_install_params: InstallParams | Missing


class PartialApplication(ObjDict):
    id: Snowflake
    name: str
    icon: str | None
    description: str
    bot_public: bool
    bot_require_code_grant: bool
    summary: str  # depreciated v11
    verify_key: str
    # team: Team | None FIXME


class Application(PartialApplication):
    rpc_origins: list[str] | Missing
    bot: User | Missing
    terms_of_service_url: str | Missing
    privacy_policy_url: str | Missing
    owner: User | Missing
    guild_id: Snowflake | Missing
    guild: PartialGuild | Missing
    primary_sku_id: Snowflake | Missing
    slug: str | Missing
    cover_image: str | Missing
    flags: ApplicationFlags | Missing
    approximate_guild_count: int | Missing
    redirect_uris: list[str] | Missing
    interactions_endpoint_url: str | Missing
    role_connections_verification_url: str | Missing
    tags: list[str] | Missing
    install_params: InstallParams | Missing
    integration_types_config: dict[ApplicationIntegrationType, ApplicationIntegrationTypeConfiguration] | Missing
    custom_install_url: str | Missing
