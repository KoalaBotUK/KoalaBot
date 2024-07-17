import discord

from dislord.discord.interactions.receiving_and_responding.interaction_response import InteractionResponse, \
    InteractionCallbackType
from dislord.discord.resources.channel.message import MessageFlags


async def handle_response(response: InteractionResponse, dpy_interaction: discord.Interaction):
    match response.type:
        case InteractionCallbackType.PONG:
            await dpy_interaction.response.pong()
        case InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE:
            await dpy_interaction.response.send_message(ephemeral=(
                        response.data.get("flags") is not None and MessageFlags.EPHEMERAL in response.data.get("flags")),
                                                        **response.data)
