from typing import Callable

from dislord.discord.interactions.application_commands.enums import ApplicationCommandOptionType
from dislord.discord.interactions.application_commands.models import ApplicationCommandOption
from dislord.discord.interactions.receiving_and_responding.interaction import Interaction
from dislord.discord.reference import Snowflake


class CommandGroup:
    name: str
    description: str
    dm_permission: bool
    nsfw: bool
    guild_id: Snowflake
    parent: 'CommandGroup' = None
    commands: dict[str, ApplicationCommandOption] = {}
    command_callbacks: dict[str, Callable] = {}

    def __init__(self, name: str = None, description: str = None,
                 dm_permission: bool = True, nsfw: bool = False, guild_id: Snowflake = None,
                 parent: 'CommandGroup' = None):
        self.name = name
        self.description = description
        self.parent = parent
        self.dm_permission = dm_permission
        self.nsfw = nsfw
        self.guild_id = guild_id

    def add_command(self, command: ApplicationCommandOption, callback: Callable):
        self.commands[command.name] = command
        self.command_callbacks[command.name] = callback

    def command(self, *, name, description, options: list[ApplicationCommandOption] = None):
        def decorator(func):
            self.add_command(ApplicationCommandOption(name=name, description=description,
                                                      type=ApplicationCommandOptionType.SUB_COMMAND,
                                                      options=options), func)
            return func

        return decorator

    def callback(self, interaction: Interaction, **kwargs):
        command_name = interaction.data.options[0].name
        kwargs = {}
        for option in interaction.data.options[0].options:
            kwargs[option.name] = option.value
        return self.command_callbacks[command_name](interaction, **kwargs)
