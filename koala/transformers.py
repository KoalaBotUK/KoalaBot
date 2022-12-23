import datetime
from typing import Union, List, Optional

import discord
from discord import app_commands, Interaction
from discord.app_commands import Choice

from . import db


class ExtensionTransformer(app_commands.Transformer):
    """
    Transformer for Koala Extensions
    """
    async def choices(self) -> Optional[List[Choice[Union[int, float, str]]]]:
        extensions = db.get_all_available_guild_extensions()
        choices = []
        for extension in extensions:
            choices.append(Choice(name=extension, value=extension))
        return choices

    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        return value


class DatetimeTransformer(app_commands.Transformer):
    """
    Transformer for ISO datetime
    """
    @staticmethod
    def convert_iso_datetime(argument):
        try:
            return datetime.datetime.fromisoformat(argument)
        except ValueError:
            raise ValueError('Invalid ISO format "%s", instead use the format "2020-01-01 00:00:00"' % argument)

    async def transform(self, interaction: discord.Interaction, value: str) -> datetime.datetime:
        return DatetimeTransformer.convert_iso_datetime(value)
