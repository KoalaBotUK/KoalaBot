class StateConfigurationException(Exception):
    MISSING_PUBLIC_TOKEN = "Public token has not been configured. Please use dislord.configure(...)"


class DiscordApiException(Exception):
    UNKNOWN_INTERACTION_TYPE = "Unknown interaction type %s"
