import discord
from discord.ext.commands import Bot

from koala.cogs.verification import db, errors
from koala.db import assign_session


@assign_session
def blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise errors.InvalidArgumentError("Please mention a role in this guild")

    db.add_to_blacklist(user_id, role.id, suffix, **kwargs)


@assign_session
def remove_blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise errors.InvalidArgumentError("Please mention a role in this guild")

    db.remove_from_blacklist(user_id, role.id, suffix, **kwargs)
