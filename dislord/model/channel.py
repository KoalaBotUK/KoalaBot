from dislord.discord.resources.channel.channel import Channel as ChannelPayload
from dislord.model.base import BaseModel


class Channel(BaseModel):
    payload: ChannelPayload

    @staticmethod
    def from_payload(payload: ChannelPayload) -> 'Channel':
        return Channel(
            payload=payload
        )
