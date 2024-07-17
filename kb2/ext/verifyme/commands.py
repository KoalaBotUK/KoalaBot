from dislord.discord.interactions.components.enums import ButtonStyle
from dislord.discord.interactions.components.models import Component, ActionRow, Button
from dislord.discord.interactions.receiving_and_responding.interaction_response import InteractionResponse
from kb2.main import client
from dislord.discord.interactions.receiving_and_responding.interaction import Interaction


@client.command(name="verifyme", description="Verify your identity with Koala")
def verify_me(interaction: Interaction):
    return InteractionResponse.message(content="Please verify yourself through the below link", components=[ActionRow(
        components=[Button(style=ButtonStyle.LINK, label="Verify", custom_id="1", url="https://koalabot.uk")])])
