from typing import Self

from dislord.types import ObjDict
from dislord.discord.interactions.receiving_and_responding.message_interaction import InteractionType
from dislord.discord.resources.application.enums import ApplicationIntegrationType
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Snowflake, Missing


class MessageInteractionMetadata(ObjDict):
    id: Snowflake
    type: InteractionType
    user: User
    authorizing_integration_owners: dict[ApplicationIntegrationType, Snowflake]
    original_response_message_id: Snowflake | Missing
    interacted_message_id: Snowflake | Missing
    triggering_interaction_metadata: Self | Missing
