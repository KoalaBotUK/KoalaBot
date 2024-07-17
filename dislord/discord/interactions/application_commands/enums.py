from enum import Enum


class ApplicationCommandType(Enum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


class ApplicationCommandOptionType(Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11

    # def from_python_type(self, type_hint):
    #     python_mapping = {str: self.STRING, int: self.INTEGER, bool: self.BOOLEAN,
    #                       User: self.USER, Channel: self.CHANNEL,
    #                       # Role: self.ROLE, Mentionable: self.MENTIONABLE, FIXME
    #                       float: self.NUMBER,
    #                       # Attachment: self.ATTACHMENT FIXME
    #                       }
    #     par = python_mapping.get(type_hint)
    #     if par is None:
    #         raise RuntimeError(f"Unexpected command param type: {type_hint}")
    #
    # def __eq__(self, other):
    #     try:
    #         return self.value == other.value
    #     except Exception:
    #         return False


class ApplicationCommandPermissionType(Enum):
    ROLE = 1
    USER = 2
    CHANNEL = 3
