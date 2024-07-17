from enum import Enum

from dislord.types import ObjDict

DISCORD_API_VERSION = 10
DISCORD_URL = f"https://discord.com/api/v{DISCORD_API_VERSION}"


class TokenType(Enum):
    BOT = "Bot"
    OAUTH2 = "Bearer"


class Authorization(ObjDict):
    token_type: TokenType
    token: str

    def to_authorization_header(self):
        return {"Authorization": f"{self.token_type.value} {self.token}"}


Snowflake = str

ISOTimestamp = type(str)  # ISO8601 Timestamp

Missing = type(None)


class Locale(Enum):
    INDONESIAN = 'id'
    DANISH = 'da'
    GERMAN = 'de'
    BRITISH_ENGLISH = 'en-GB'
    AMERICAN_ENGLISH = 'en-US'
    SPAIN_SPANISH = 'es-ES'
    FRENCH = 'fr'
    CROATIAN = 'hr'
    ITALIAN = 'it'
    LITHUANIAN = 'lt'
    HUNGARIAN = 'hu'
    DUTCH = 'nl'
    NORWEGIAN = 'no'
    POLISH = 'pl'
    BRAZIL_PORTUGUESE = 'pt-BR'
    ROMANIAN = 'ro'
    FINNISH = 'fi'
    SWEDISH = 'sv-SE'
    VIETNAMESE = 'vi'
    TURKISH = 'tr'
    CZECH = 'cs'
    GREEK = 'el'
    BULGARIAN = 'bg'
    RUSSIAN = 'ru'
    UKRAINIAN = 'uk'
    HINDI = 'hi'
    THAI = 'th'
    CHINESE = 'zh-CN'
    JAPANESE = 'ja'
    TAIWAN_CHINESE = 'zh-TW'
    KOREAN = 'ko'

    def __str__(self) -> str:
        return self.value
