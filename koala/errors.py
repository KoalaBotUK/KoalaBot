

class KoalaException(Exception):
    """
    The base exception for all of koala
    """
    pass


class InvalidArgumentError(KoalaException):
    """
    Invalid Argument provided by the user
    """
    pass
