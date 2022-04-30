from sqlalchemy import text

from koala.enums import DatabaseType
from koala.env import DB_TYPE


def value_suffix_like_column(value, column):
    """
    Creates a sqlalchemy where query value for a given value that contains
    a suffix which is found in the db

    example:

        value_suffix_like_column(":email", "email_suffix")

        text(":email like ('%' || email_suffix)")       SQLITE
        text(":email like CONCAT('%', email_suffix)")   MYSQL

    :param value: full value, or alias
    :param column: column name
    :return:
    """
    if DB_TYPE == DatabaseType.SQLITE:
        return text(f"{value} like ('%' || {column})")
    else:
        return text(f"{value} like CONCAT('%', {column})")
