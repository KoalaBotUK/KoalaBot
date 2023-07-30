from koala.errors import KoalaException


class ReactForRoleException(KoalaException):
    """
    Unspecified error within the 'ReactForRole' extension
    """
    pass


class PermissionsException(ReactForRoleException):
    """
    Koala has missing permissions
    """
    pass
