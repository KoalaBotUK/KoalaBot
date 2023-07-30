from dataclasses import dataclass
from typing import List

import discord
import emoji
from discord import PartialEmoji


@dataclass
class ReactRole:
    emoji: str
    role_id: int

    def to_tuple(self, guild: discord.Guild):
        return self.emoji, guild.get_role(self.role_id)

    def partial_emoji(self):
        return PartialEmoji.from_str(emoji.emojize(self.emoji))


@dataclass
class ReactMessage:
    message_id: int
    guild_id: int
    channel_id: int
    title: str
    description: str
    colour: str
    thumbnail: str
    inline: bool
    roles: List[ReactRole]


@dataclass
class RequiredRoles:
    guild_id: int
    role_ids: List[int]
