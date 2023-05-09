import dataclasses


@dataclasses.dataclass
class ApiError:
    error: str
    message: str


@dataclasses.dataclass
class StringApiResponse:
    message: str
