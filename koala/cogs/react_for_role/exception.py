import enum

from koala.exception import KoalaException, KoalaErrorCode


class ReactionErrorCode(KoalaErrorCode):
    UNKNOWN_MEMBER_REACTION = "Unknown Member Reaction - userId: %s, guildId: %s"
    UNKNOWN_CHANNEL_REACTION = "Unknown Channel Reaction - channelId: %s, guildId: %s"
    UNKNOWN_MESSAGE_REACTION = "Unknown Message Reaction - messageId: %s, guildId: %s"
    UNKNOWN_REACTION_FIELD = "Unknown Reaction Field - messageId: %s, guildId: %s"
    UNKNOWN_REACTION_ROLE = "Unknown Reaction Role - roleId: %s, guildId: %s"


class ReactionException(KoalaException):
    pass
