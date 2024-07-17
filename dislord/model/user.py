from typing import Self

from dislord.discord.resources.user.user import User as UserPayload
from dislord.model.base import BaseModel


class User(BaseModel):
    payload: UserPayload

    @staticmethod
    def from_payload(payload: UserPayload) -> 'User':
        return User(
            payload=payload
        )
