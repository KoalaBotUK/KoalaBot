import enum


class KoalaErrorCode(enum.Enum):
    """
    Base ErrorCodes for KoalaBot
    """
    pass


class KoalaException(Exception):
    """
    Base Exception for KoalaBot
    """
    def __init__(self, error_code: KoalaErrorCode, *args):
        self.error_code = error_code
        self.message = error_code.value.format(*args)

    def __str__(self):
        return self.message
