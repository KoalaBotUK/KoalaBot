from dislord import CommandGroup
from dislord.discord.interactions.receiving_and_responding.interaction import Interaction
from dislord.discord.interactions.receiving_and_responding.interaction_response import InteractionResponse
from kb2.main import client

koala_group = CommandGroup(name="koala", description="KoalaBot Base Commands")


@koala_group.command(name="support", description="KoalaBot Support server link")
def support(interaction: Interaction):
    return InteractionResponse.message(
        content="Join our support server for more help! https://discord.gg/5etEjVd")


client.register_group(koala_group)
