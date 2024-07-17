from dislord.discord.interactions.receiving_and_responding.interaction_response import InteractionCallbackType
from kb2.ext.koala import commands


def test_support():
    response = commands.support(None)
    assert response.type == InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE
    assert response.data.content == "Join our support server for more help! https://discord.gg/5etEjVd"
