from koala.errors import KoalaException


class VerifyException(KoalaException):
    """
    Unspecified error within the 'verify' extension
    """
    pass


class VerifyExistsException(VerifyException):
    """
    Verify already exists
    """
    pass
