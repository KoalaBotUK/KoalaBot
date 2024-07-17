from enum import IntFlag

from dislord.types import ObjDict
from dislord.discord.resources.emoji.emoji import Emoji
from dislord.discord.reference import Snowflake, Missing


class PromptType(IntFlag):
    MULTIPLE_CHOICE = 0
    DROPDOWN = 1


class OnboardingMode(IntFlag):
    ONBOARDING_DEFAULT = 0
    ONBOARDING_ADVANCED = 1


class PromptOption(ObjDict):
    id: Snowflake
    channel_ids: list[Snowflake]
    role_ids: list[Snowflake]
    emoji: Emoji | Missing
    emoji_id: Snowflake | Missing
    emoji_name: str | Missing
    emoji_animated: bool | Missing
    title: str
    description: str


class OnboardingPrompt(Snowflake):
    id: Snowflake
    type: PromptType
    options: list[PromptOption]
    title: str
    single_select: bool
    required: bool
    in_onboarding: bool


class GuildOnboarding(ObjDict):
    guild_id: Snowflake
    prompts: list[OnboardingPrompt]
    default_channel_ids: list[Snowflake]
    enabled: bool
    mode: OnboardingMode
