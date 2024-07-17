from dislord.discord.resources.application.models import Application as ApplicationPayload
from dislord.model.base import BaseModel


class Application(BaseModel):
    payload: ApplicationPayload

    @staticmethod
    def from_payload(payload: ApplicationPayload) -> 'Application':
        return Application(
            payload=payload
        )

