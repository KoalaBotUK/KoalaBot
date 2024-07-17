from dislord.discord.resources.guild.guild import Guild as GuildPayload
from dislord.model.base import BaseModel


class Guild(GuildPayload):

    @staticmethod
    def from_payload(payload: GuildPayload) -> 'Guild':
        return Guild(
            **payload
        )


