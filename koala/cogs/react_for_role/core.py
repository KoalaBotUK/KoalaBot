from ast import Tuple
import datetime
from typing import *

import discord
from discord.ext.commands import Bot
from discord.ext import commands
import emoji

from . import db2
from .log import logger

from koala.db import assign_session
import discord
from discord import Colour
from koala.colours import KOALA_GREEN
from .utils import CUSTOM_EMOJI_REGEXP, UNICODE_EMOJI_REGEXP
# Constants

koala_logo = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"

# Variables
# current_activity = None

def create_ctx(bot: Bot, guild: discord.Guild):
    return { 'bot': bot, 'guild': guild }

@assign_session
async def create_rfr_message(title: str, guild: discord.Guild, description: str, colour: Colour, channel: discord.TextChannel, **kwargs):
    embed: discord.Embed = discord.Embed(title=title, description=description, colour=colour)
    embed.set_footer(text="ReactForRole")
    embed.set_thumbnail(url=koala_logo)
    rfr_msg: discord.Message = await channel.send(embed=embed)
    db2.add_rfr_message(guild.id, channel.id, rfr_msg.id, **kwargs)
    return rfr_msg

@assign_session
async def delete_rfr_message(guild_id: str, channel_id: str, msg: discord.Message, **kwargs):
    rfr_msg_row = db2.get_rfr_message(guild_id, channel_id, msg.id, **kwargs)
    db2.remove_rfr_message_emoji_roles(rfr_msg_row[3], **kwargs)
    db2.remove_rfr_message(guild_id, channel_id, msg.id, **kwargs)
    await msg.delete()

@assign_session
async def use_inline_rfr_all(guild: discord.Guild, **kwargs):
    text_channels: List[discord.TextChannel] = guild.text_channels
    guild_rfr_messages = db2.get_guild_rfr_messages(guild.id, **kwargs)
    for rfr_message in guild_rfr_messages:
        channel: discord.TextChannel = discord.utils.get(text_channels, id=rfr_message[1])
        msg: discord.Message = await channel.fetch_message(id=rfr_message[2])
        embed: discord.Embed = get_embed_from_message(msg)
        length = get_number_of_embed_fields(embed)
        for i in range(length):
            field = embed.fields[i]
            embed.set_field_at(i, name=field.name, value=field.value, inline=True)
        await msg.edit(embed=embed)

async def use_inline_rfr_specific(embed: discord.Embed, msg: discord.Message):
    length = get_number_of_embed_fields(embed)
    for i in range(length):
        field = embed.fields[i]
        embed.set_field_at(i, name=field.name, value=field.value, inline=True)
    await msg.edit(embed=embed)

async def rfr_edit(embed: discord.Embed, msg: discord.Message, description: str = "", title: str = "", image_url: str = ""):
    embed.description = description
    embed.title = title
    embed.set_thumbnail(url=image_url)
    await msg.edit(embed=embed)
    return msg

@assign_session
async def rfr_remove_emojis_roles(bot: Bot, guild: discord.Guild, msg: discord.Message, rfr_msg_row: discord.Message, wanted_removals: List[Union[discord.Emoji, str, discord.Role]], **kwargs):
    rfr_embed: discord.Embed = get_embed_from_message(msg)
    rfr_embed_fields = rfr_embed.fields
    new_embed = discord.Embed(title=rfr_embed.title, description=rfr_embed.description,
                                colour=KOALA_GREEN)
    new_embed.set_thumbnail(
        url=koala_logo)
    new_embed.set_footer(text="ReactForRole")
    removed_field_indexes = []
    reactions_to_remove: List[discord.Reaction] = []
    errors = []

    for row in wanted_removals:
        if isinstance(row, discord.Emoji) or isinstance(row, str):
            field_index = [x.name for x in rfr_embed_fields].index(str(row))
            if isinstance(row, str):
                db2.remove_rfr_message_emoji_role(rfr_msg_row[3], emoji_raw=emoji.demojize(row), **kwargs)
            else:
                db2.remove_rfr_message_emoji_role(rfr_msg_row[3], emoji_raw=row, **kwargs)
        else:
            # row is instance of role
            field_index = [x.value for x in rfr_embed_fields].index(row.mention)
            db2.remove_rfr_message_emoji_role(rfr_msg_row[3], role_id=row.id, **kwargs)

        field = rfr_embed_fields[field_index]
        removed_field_indexes.append(field_index)
        reaction_emoji, err = get_first_emoji_from_str(bot, guild, field.name)
        if (err != None):
            errors.append(err)
        reaction: discord.Reaction = [x for x in msg.reactions if str(x.emoji) == str(reaction_emoji)][0]
        reactions_to_remove.append(reaction)

    new_embed_fields = [field for field in rfr_embed_fields if
                        rfr_embed_fields.index(field) not in removed_field_indexes]

    for field in new_embed_fields:
        new_embed.add_field(name=field.name, value=field.value, inline=False)
    
    for reaction in reactions_to_remove:
        await reaction.clear()
    await msg.edit(embed=new_embed)
    
    return new_embed, errors


@assign_session
async def rfr_add_emoji_role(guild: str, channel: discord.TextChannel, rfr_embed: discord.Embed, msg: discord.Message, rfr_msg_row: discord.Message, emoji_role_map: List[Tuple[Union[discord.Emoji, str], discord.Role]], **kwargs):
    duplicateRolesFound = False
    duplicateEmojisFound = False

    for emoji_role in emoji_role_map:
        discord_emoji = emoji_role[0]
        role = emoji_role[1]

        if discord_emoji in [x.name for x in rfr_embed.fields]:
             duplicateEmojisFound = True
        elif role in [x.value for x in rfr_embed.fields]:
             duplicateRolesFound = True
        else:
            if isinstance(discord_emoji, str):
                db2.add_rfr_message_emoji_role(rfr_msg_row[3], emoji.demojize(discord_emoji),
                                                                        role.id, **kwargs)
            else:
                db2.add_rfr_message_emoji_role(rfr_msg_row[3], str(discord_emoji), role.id, **kwargs)
            rfr_embed.add_field(name=str(discord_emoji), value=role.mention, inline=False)
            await msg.add_reaction(discord_emoji)

            if isinstance(discord_emoji, str):
                logger.info(
                    f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                    f"({str(channel.id)}, {str(guild.id)}) with emoji {discord_emoji}.")
            else:
                logger.info(
                    f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                    f"({str(channel.id)}, {str(guild.id)}) with emoji {discord_emoji.id}.")

    edited_msg = await msg.edit(embed=rfr_embed)
    return duplicateRolesFound, duplicateEmojisFound, edited_msg

async def add_guild_rfr_required_role(bot: Bot, guild: discord.Guild, role_str: str, **kwargs):
    ctx = create_ctx(bot, guild)
    role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
    db2.remove_guild_rfr_required_role(ctx.guild.id, role.id, **kwargs)
    return role

async def remove_guild_rfr_required_role(bot: Bot, guild: discord.Guild, role_str: str, **kwargs):
    ctx = create_ctx(bot, guild)
    role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
    db2.add_guild_rfr_required_role(ctx.guild.id, role.id, **kwargs)
    return role

def rfr_list_guild_required_roles(guild: discord.Guild, **kwargs):
    return db2.get_guild_rfr_required_roles(guild.id, **kwargs)

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
    if not msg:
        return None
    try:
        embed = msg.embeds[0]
        if not embed:
            return None
        return embed
    except IndexError:
        return None

def get_number_of_embed_fields(embed: discord.Embed) -> int:
    """
    Gets the number of fields in an embed.
    :param embed: Embed to check
    :return: Number of embed fields.
    """
    return len(embed.fields)


async def get_first_emoji_from_str(bot: Bot, guild: discord.Guild, content: str) -> Optional[
    Union[discord.Emoji, str]]:
    """
    Gets the first emoji in a string input, custom or not. Doesn't work with custom emojis the bot doesn't have
    access to.
    :param ctx: Context of the original command
    :param content: Message content
    :return: Emoji if there is a valid one. Otherwise None.
    """

    ctx = create_ctx(bot, guild)

    # First check for a custom discord emoji in the string
    search_result = CUSTOM_EMOJI_REGEXP.search(str(content))
    if not search_result:
        # Check for a unicode emoji in the string
        search_result = UNICODE_EMOJI_REGEXP.search(content)
        if not search_result:
            return None, "No emoji found."
        return content, None
    else:
        emoji_str = search_result.group().strip()
        try:
            discord_emoji: discord.Emoji = await commands.EmojiConverter().convert(ctx, emoji_str)
            return discord_emoji, None
        except commands.CommandError:
            return None, "An error occurred when trying to get the emoji. Please contact the bot developers for support."
        except commands.BadArgument:
            return None, "Couldn't get the emoji you used - is it from this server or a server I'm in?"