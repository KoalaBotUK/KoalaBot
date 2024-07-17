import json
from typing import Callable

from discord_interactions import verify_key, InteractionType

from .discord.interactions.application_commands.enums import ApplicationCommandType
from .discord.interactions.application_commands.models import ApplicationCommandOption
from .discord.interactions.receiving_and_responding.interaction import Interaction
from .discord.interactions.receiving_and_responding.interaction_response import InteractionResponse
from .discord.reference import Snowflake, Missing
from .discord.resources.application.models import Application
from .group import CommandGroup
from .api import DiscordApi
from .error import DiscordApiException
from .model.api import HttpResponse, HttpUnauthorized, HttpOk
from .model.base import cast, EnhancedJSONEncoder
from .model.channel import Channel
from .model.commands import ApplicationCommand
from .model.guild import Guild
from .model.user import User


class ApplicationClient:
    _public_key: str
    _api: DiscordApi
    _commands: dict[Snowflake, dict[str, ApplicationCommand]] = {}
    _command_callbacks: dict[str, Callable] = {}
    _application: Application = Missing()
    _guilds: list[Guild] = Missing()

    def __init__(self, public_key, bot_token):
        self._public_key = public_key
        self._api = DiscordApi(self, bot_token)

    def verified_interact(self, raw_request, signature, timestamp) -> HttpResponse:
        if signature is None or timestamp is None or not verify_key(json.dumps(raw_request, separators=(',', ':'))
                                                                            .encode('utf-8'), signature, timestamp,
                                                                    self._public_key):
            return HttpUnauthorized('Bad request signature')
        return self.interact(raw_request)

    def interact(self, raw_request) -> HttpResponse:
        interaction = cast(raw_request, Interaction, self)

        if interaction.type == InteractionType.PING:  # PING
            response_data = InteractionResponse.pong()  # PONG
        elif interaction.type == InteractionType.APPLICATION_COMMAND:
            data = interaction.data
            command_name = data.name
            kwargs = {}
            for option in data.options:
                kwargs[option.name] = option.value
            response_data = self._command_callbacks[command_name](interaction=interaction, **kwargs)

        else:
            raise DiscordApiException(DiscordApiException.UNKNOWN_INTERACTION_TYPE.format(interaction.type))

        return HttpOk(json.loads(json.dumps(response_data, cls=EnhancedJSONEncoder)), headers={"Content-Type": "application/json"})

    def add_command(self, command: ApplicationCommand, callback: Callable):
        if self._commands.get(command.guild_id) is None:
            self._commands[command.guild_id] = {}
        self._command_callbacks[command.name] = callback
        self._commands.get(command.guild_id)[command.name] = command

    def command(self, *, name, description, dm_permission=True, nsfw=False, guild_ids: list[Snowflake] = None,
                options: list[ApplicationCommandOption] = None):
        if guild_ids is None:
            guild_ids = ["ALL"]

        def decorator(func):
            for guild_id in guild_ids:
                if guild_id == "ALL":
                    guild_id = None
                self.add_command(ApplicationCommand(name=name, description=description,
                                                    type=ApplicationCommandType.CHAT_INPUT,
                                                    dm_permission=dm_permission, nsfw=nsfw,
                                                    guild_id=guild_id, options=options, client=self), func)
            return func

        return decorator

    def register_group(self, command_group: CommandGroup):
        if self._commands.get(command_group.guild_id) is None:
            self._commands[command_group.guild_id] = {}

        self._commands[command_group.guild_id][command_group.name] = ApplicationCommand(
            name=command_group.name, description=command_group.description, type=ApplicationCommandType.CHAT_INPUT,
            dm_permission=command_group.dm_permission, nsfw=command_group.nsfw, guild_id=command_group.guild_id,
            options=list(command_group.commands.values()), client=self)

        self._command_callbacks[command_group.name] = command_group.callback

    def serverless_handler(self, event, context):
        if event['httpMethod'] == "POST":
            print(f"🫱 Full Event: {event}")
            raw_request = json.loads(event["body"])
            print(f"👉 Request: {raw_request}")
            raw_headers = event["headers"]
            signature = raw_headers.get('x-signature-ed25519')
            timestamp = raw_headers.get('x-signature-timestamp')
            response = self.verified_interact(raw_request, signature, timestamp).as_serverless_response()
            print(f"🫴 Response: {response}")
            return response

    @property
    def application(self):
        if self._application is Missing():
            self._application = self.get_application()
        return self._application

    @property
    def guilds(self) -> list[Guild]:
        if self._guilds is Missing():
            self._guilds = self._get_guilds()
        return self._guilds

    def get_application(self):
        return self._api.get("/applications/@me", type_hint=Application)

    def sync_commands(self, guild_id: Snowflake = None, guild_ids: list[Snowflake] = None,
                      application_id: Snowflake = None):
        if guild_ids:
            for g_id in guild_ids:
                self.sync_commands(guild_id=g_id, application_id=application_id)

        registered_commands = self._get_commands(guild_id)
        client_commands = self._commands.get(guild_id)
        missing_commands = list(client_commands.values()) if client_commands else []
        for registered_command in registered_commands:
            if registered_command not in missing_commands:
                self._delete_commands(command_id=registered_command.id, guild_id=guild_id,
                                      application_id=registered_command.application_id)
            else:
                missing_commands.remove(registered_command)

        for missing_command in missing_commands:
            self._register_command(missing_command, guild_id=guild_id, application_id=application_id)

    def _get_commands(self, guild_id: Snowflake = None, application_id: Snowflake = None,
                      with_localizations: bool = None) -> list[ApplicationCommand]:
        endpoint = f"/applications/{application_id if application_id else self.application.id}"
        if guild_id:
            endpoint += f"/guilds/{guild_id}"

        params = {}
        if with_localizations is not None:
            params["with_localizations"] = with_localizations

        return [ApplicationCommand(**p) for p in self._api.get(f"{endpoint}/commands", params=params,
                                                               type_hint=list[ApplicationCommand])]

    def _delete_commands(self, command_id: Snowflake,
                         guild_id: Snowflake = None, application_id: Snowflake = None) -> None:
        endpoint = f"/applications/{application_id if application_id else self.application.id}"
        if guild_id:
            endpoint += f"/guilds/{guild_id}"

        self._api.delete(f"{endpoint}/commands/{command_id}")

    def _register_command(self, application_command: ApplicationCommand,
                          guild_id: Snowflake = None, application_id: Snowflake = None) -> ApplicationCommand:
        endpoint = f"/applications/{application_id if application_id else self.application.id}"
        if guild_id:
            endpoint += f"/guilds/{guild_id}"
        return ApplicationCommand(**self._api.post(f"{endpoint}/commands", application_command.to_payload(),
                                                   type_hint=ApplicationCommand))

    def get_user(self, user_id=None) -> User:
        return User.from_payload(self._api.get(f"/users/{user_id if user_id else '@me'}"))

    def get_guild(self, guild_id) -> Guild:
        return Guild.from_payload(self._api.get(f"/guilds/{guild_id}"))

    def _get_guilds(self) -> list[Guild]:
        return [Guild.from_payload(p) for p in self._api.get("/users/@me/guilds")]

    def get_channel(self, channel_id) -> list[Channel]:
        return [Channel.from_payload(p) for p in self._api.get(f"/channels/{channel_id}")]
