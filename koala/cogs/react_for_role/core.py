import datetime
from typing import List, Optional

import discord
from discord.ext.commands import Bot

from . import db2
from .log import logger

from koala.db import assign_session
import discord
from discord import Colour
# Constants

koala_logo = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"

# Variables
# current_activity = None

@assign_session
async def create_rfr_message(title: str, guild: discord.Guild, description: str, colour: Colour, channel: discord.TextChannel, **kwargs):
  embed: discord.Embed = discord.Embed(title=title, description=description, colour=colour)
  embed.set_footer(text="ReactForRole")
  embed.set_thumbnail(url=koala_logo)
  rfr_msg: discord.Message = await channel.send(embed=embed)
  db2.add_rfr_message(guild.id, channel.id, rfr_msg.id, **kwargs)
  return rfr_msg


async def setup_rfr_reaction_permissions(guild: discord.Guild, channel: discord.TextChannel, bot: Bot):
  """
  Overwrites a text channel's reaction perms so that nobody can add new reactions to any message sent in the
  channel, only the bot, to make sure people don't mess with the system. Relies on roles tending not to be added/
  removed constantly to keep performance satisfactory.
  :param guild: Guild that the rfr message is in
  :param channel: Channel that the rfr message is in
  :return:
  """
  #  Get the @everyone role.
  role: discord.Role = discord.utils.get(guild.roles, id=guild.id)
  overwrite: discord.PermissionOverwrite = discord.PermissionOverwrite()
  overwrite.update(add_reactions=False)
  # TODO - tests fail here with 403, missing 'manage_roles' permission
  await channel.set_permissions(role, overwrite=overwrite)
  bot_members = [member for member in guild.members if member.bot and member.id == bot.user.id]
  overwrite.update(add_reactions=True)
  for bot_member in bot_members:
      await channel.set_permissions(bot_member, overwrite=overwrite)

def get_embed_from_message(msg: discord.Message) -> Optional[discord.Embed]:
    """
    Gets the embed from a given message
    :param msg: Message to check
    :return: Returns the embed if there is one. If there isn't returns None
    """

    # TODO: Figure out a way to get this working in core

    if not msg:
        return None
    try:
        embed = msg.embeds[0]
        if not embed:
            return None
        return embed
    except IndexError:
        return None
