import dataclasses


@dataclasses.dataclass
class ApiError:
    error: str
    description: str
