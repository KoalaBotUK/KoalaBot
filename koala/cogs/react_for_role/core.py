from typing import *

import discord
import emoji
from discord.ext import commands
from discord.ext.commands import Bot

import koalabot
from koala.db import assign_session
from . import db
from .db import get_rfr_message
from .dto import ReactMessage, ReactRole, RequiredRoles
from .errors import PermissionsException
from .log import logger
from .utils import CUSTOM_EMOJI_REGEXP, UNICODE_EMOJI_REGEXP, FLAG_EMOJI_REGEXP
from ...errors import KoalaException

# Constants

koala_logo = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"


# Variables
# current_activity = None

def create_ctx(bot: Bot, guild: discord.Guild):
    return {'bot': bot, 'guild': guild}


@assign_session
async def get_rfr_message_dto(bot: koalabot.KoalaBot, message_id: int, guild_id: int, channel_id: int,
                              **kwargs):
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    message: discord.Message = await channel.fetch_message(message_id)

    rfr_embed = get_embed_from_message(message)

    _, _, _, emoji_role_id = db.get_rfr_message(guild_id, channel_id, message_id, **kwargs)
    roles_list = db.get_rfr_message_emoji_roles(emoji_role_id, **kwargs)

    return ReactMessage(
        message_id=message_id,
        guild_id=guild_id,
        channel_id=channel_id,
        title=rfr_embed.title,
        description=rfr_embed.description,
        thumbnail=rfr_embed.thumbnail.url,
        colour=rfr_embed.colour.__str__(),
        inline=len(rfr_embed.fields) > 0 and rfr_embed.fields[0].inline,
        roles=[ReactRole(role[1], role[2]) for role in roles_list]
    )


@assign_session
async def create_rfr_message(bot: koalabot.KoalaBot, guild_id: int, channel_id: int, title: str, description: str,
                             colour: discord.Colour, thumbnail: str = None, inline: bool = None,
                             roles: List[Tuple[Union[discord.Emoji, str], discord.Role]] = None,
                             **kwargs) -> ReactMessage:
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    # await overwrite_channel_add_reaction_perms(bot, guild, channel)

    embed: discord.Embed = discord.Embed(title=title, description=description, colour=colour)
    embed.set_footer(text="ReactForRole")
    if thumbnail is None:
        embed.set_thumbnail(url=koala_logo)
    else:
        embed.set_thumbnail(url=thumbnail)

    rfr_msg: discord.Message = await channel.send(embed=embed)
    db.add_rfr_message(guild_id, channel_id, rfr_msg.id, **kwargs)

    if roles is not None:
        await rfr_add_emoji_role(guild, channel, rfr_msg, roles, **kwargs)

    if inline:
        await use_inline_rfr_specific(rfr_msg)
    return await get_rfr_message_dto(bot, rfr_msg.id, guild_id, channel_id, **kwargs)


@assign_session
async def update_rfr_message(bot: koalabot.KoalaBot, message_id: int, guild_id: int, channel_id: int,
                             title: str, description: str, colour: discord.Colour,
                             thumbnail: str, inline: bool = None,
                             roles: List[Tuple[Union[discord.Emoji, str], discord.Role]] = None,
                             **kwargs):
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)

    if roles is not None:
        await rfr_edit_emoji_role(bot, message_id, guild_id, channel_id, roles, **kwargs)

    await rfr_edit(await channel.fetch_message(message_id), title=title, description=description, thumbnail_url=thumbnail, colour=colour)

    if inline is not None:
        await use_inline_rfr_specific(await channel.fetch_message(message_id))

    return await get_rfr_message_dto(bot, message_id, guild_id, channel_id, **kwargs)


@assign_session
async def delete_rfr_message(bot: koalabot.KoalaBot, message_id: int, guild_id: int, channel_id: int, **kwargs):
    rfr_msg_row = db.get_rfr_message(guild_id, channel_id, message_id, **kwargs)
    db.remove_rfr_message_emoji_roles(rfr_msg_row[3], **kwargs)
    db.remove_rfr_message(guild_id, channel_id, message_id, **kwargs)

    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    message = await channel.fetch_message(message_id)

    await message.delete()


@assign_session
async def use_inline_rfr_all(guild: discord.Guild, **kwargs):
    text_channels: List[discord.TextChannel] = guild.text_channels
    guild_rfr_messages = db.get_guild_rfr_messages(guild.id, **kwargs)
    for rfr_message in guild_rfr_messages:
        channel: discord.TextChannel = discord.utils.get(text_channels, id=rfr_message[1])
        msg: discord.Message = await channel.fetch_message(rfr_message[2])
        embed: discord.Embed = get_embed_from_message(msg)
        length = get_number_of_embed_fields(embed)
        for i in range(length):
            field = embed.fields[i]
            embed.set_field_at(i, name=field.name, value=field.value, inline=True)
        await msg.edit(embed=embed)


async def use_inline_rfr_specific(msg: discord.Message):
    rfr_embed = get_embed_from_message(msg)
    length = get_number_of_embed_fields(rfr_embed)
    for i in range(length):
        field = rfr_embed.fields[i]
        rfr_embed.set_field_at(i, name=field.name, value=field.value, inline=True)
    await msg.edit(embed=rfr_embed)


async def rfr_edit(message: discord.Message, *,
                   title: str = None, description: str = None, thumbnail_url: str = None, colour: discord.Colour = None):
    embed = get_embed_from_message(message)
    if title is not None:
        embed.title = title
    if description is not None:
        embed.description = description
    if thumbnail_url is not None:
        embed.set_thumbnail(url=thumbnail_url)
    if colour is not None:
        embed.colour = colour
    return await message.edit(embed=embed)


@assign_session
async def rfr_remove_emojis_roles(bot: Bot, guild: discord.Guild, msg: discord.Message,
                                  rfr_msg_row: Tuple[int, int, int, int],
                                  wanted_removals: List[Union[discord.Emoji, str, discord.Role]], **kwargs):
    rfr_embed: discord.Embed = get_embed_from_message(msg)
    rfr_embed_fields = rfr_embed.fields
    new_embed = rfr_embed.copy()
    new_embed.clear_fields()
    removed_field_indexes = []
    reactions_to_remove: List[discord.Reaction] = []
    errors = []

    for row in wanted_removals:
        if isinstance(row, discord.Emoji) or isinstance(row, str):
            field_index = [x.name for x in rfr_embed_fields].index(str(row))
            if isinstance(row, str):
                db.remove_rfr_message_emoji_role(rfr_msg_row[3], emoji_raw=emoji.demojize(row), **kwargs)
            else:
                db.remove_rfr_message_emoji_role(rfr_msg_row[3], emoji_raw=row, **kwargs)
        else:
            # row is instance of role
            field_index = [x.value for x in rfr_embed_fields].index(row.mention)
            db.remove_rfr_message_emoji_role(rfr_msg_row[3], role_id=row.id, **kwargs)

        field = rfr_embed_fields[field_index]
        removed_field_indexes.append(field_index)
        reaction_emoji, err = await get_first_emoji_from_str(bot, guild, field.name)
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
async def rfr_edit_emoji_role(bot: koalabot.KoalaBot, message_id: int, guild_id: int, channel_id: int,
                              emoji_role_map: List[Tuple[Union[discord.Emoji, str], discord.Role]],
                              **kwargs):
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)

    _, _, _, emoji_role_id = db.get_rfr_message(guild_id, channel_id, message_id, **kwargs)
    emoji_roles = db.get_rfr_message_emoji_roles(emoji_role_id, **kwargs)
    remove_role_map = {emoji.emojize(r[1]): guild.get_role(r[2]) for r in emoji_roles}
    add_role_map = {}

    for emoji_str, role in emoji_role_map:
        if emoji.emojize(emoji_str) in remove_role_map.keys():
            remove_role_map.pop(emoji.emojize(emoji_str))
        else:
            add_role_map[emoji.emojize(emoji_str)] = role

    remove_role_map = [(r, remove_role_map.get(r)) for r in remove_role_map.keys()]
    add_role_map = [(r, add_role_map.get(r)) for r in add_role_map.keys()]

    if remove_role_map:
        await rfr_remove_emojis_roles(bot, guild, await channel.fetch_message(message_id), get_rfr_message(guild_id, channel_id, message_id, **kwargs),
                                      [r[1] for r in remove_role_map], **kwargs)

    if add_role_map:
        await rfr_add_emoji_role(guild, channel, await channel.fetch_message(message_id), add_role_map, **kwargs)


@assign_session
async def rfr_add_emoji_role(guild: discord.Guild, channel: discord.TextChannel,
                             msg: discord.Message, emoji_role_map: List[Tuple[Union[discord.Emoji, str], discord.Role]],
                             **kwargs):
    rfr_embed = get_embed_from_message(msg)
    duplicate_roles_found = False
    duplicate_emojis_found = False
    rfr_msg_row = db.get_rfr_message(guild.id, channel.id, msg.id)

    for emoji_role in emoji_role_map:
        discord_emoji = emoji_role[0]
        role = emoji_role[1]

        if discord_emoji in [x.name for x in rfr_embed.fields]:
            duplicate_emojis_found = True
        elif role in [x.value for x in rfr_embed.fields]:
            duplicate_roles_found = True
        else:
            if isinstance(discord_emoji, str):
                db.add_rfr_message_emoji_role(rfr_msg_row[3], emoji.demojize(discord_emoji),
                                              role.id, **kwargs)
            else:
                db.add_rfr_message_emoji_role(rfr_msg_row[3], str(discord_emoji), role.id, **kwargs)
            rfr_embed.add_field(name=str(discord_emoji), value=role.mention, inline=False)
            await msg.add_reaction(discord_emoji)

            if isinstance(discord_emoji, str):
                logger.info(
                    f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                    f"({str(channel.id)}, {str(guild.id)}) with emoji {emoji.demojize(discord_emoji)}.")
            else:
                logger.info(
                    f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                    f"({str(channel.id)}, {str(guild.id)}) with emoji {discord_emoji.id}.")

    edited_msg = await msg.edit(embed=rfr_embed)
    return duplicate_roles_found, duplicate_emojis_found, edited_msg


@assign_session
def edit_guild_rfr_required_roles(bot: koalabot.KoalaBot, guild_id: int, role_ids: List[int], **kwargs):
    guild = bot.get_guild(guild_id)

    add_role_ids = []
    remove_role_ids: List = rfr_list_guild_required_roles(guild, **kwargs).role_ids

    for role_id in role_ids:
        if role_id in remove_role_ids:
            remove_role_ids.remove(role_id)
        else:
            add_role_ids.append(role_id)

    for role_id in remove_role_ids:
        remove_guild_rfr_required_role(guild, role_id, **kwargs)

    for role_id in add_role_ids:
        add_guild_rfr_required_role(guild, role_id, **kwargs)


def add_guild_rfr_required_role(guild: discord.Guild, role_id: int, **kwargs):
    db.add_guild_rfr_required_role(guild.id, role_id, **kwargs)


def remove_guild_rfr_required_role(guild: discord.Guild, role_id: int, **kwargs):
    db.remove_guild_rfr_required_role(guild.id, role_id, **kwargs)


def rfr_list_guild_required_roles(guild: discord.Guild, **kwargs):
    return RequiredRoles(guild.id, db.get_guild_rfr_required_roles(guild.id, **kwargs))


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


async def get_first_emoji_from_str(bot: Bot, guild: discord.Guild,
                                   content: str) -> Tuple[Optional[Union[discord.Emoji, str]], Optional[str]]:
    """
    Gets the first emoji in a string input, custom or not. Doesn't work with custom emojis the bot doesn't have
    access to.
    :param bot:
    :param guild:
    :param content: Message content
    :return: Emoji if there is a valid one. Otherwise None.
    """

    # First check for a custom discord emoji in the string
    search_result = CUSTOM_EMOJI_REGEXP.search(str(content))
    if search_result:
        emoji_id = int(search_result[:-1].split(":")[-1])
        try:
            discord_emoji: discord.Emoji = await guild.fetch_emoji(emoji_id)
            if discord_emoji is None:
                discord_emoji: discord.Emoji = bot.get_emoji(emoji_id)
            return discord_emoji, None
        except commands.CommandError:
            return None, "An error occurred when trying to get the emoji. Please contact the bot developers for support."
        except commands.BadArgument:
            return None, "Couldn't get the emoji you used - is it from this server or a server I'm in?"

    # Check for a unicode emoji in the string
    search_result = UNICODE_EMOJI_REGEXP.search(content)
    search_result_flag = FLAG_EMOJI_REGEXP.search(content)
    if search_result or search_result_flag:
       return content, None

    return None, "No emoji found."


async def overwrite_channel_add_reaction_perms(bot: Bot, guild: discord.Guild, channel: discord.TextChannel):
    """
    Overwrites a text channel's reaction perms so that nobody can add new reactions to any message sent in the
    channel, only the bot, to make sure people don't mess with the system. Relies on roles tending not to be added/
    removed constantly to keep performance satisfactory.
    :param guild: Guild that the rfr message is in
    :param channel: Channel that the rfr message is in
    :return:
    """
    try:
        #  Get the @everyone role.
        role: discord.Role = discord.utils.get(guild.roles, id=guild.id)
        overwrite: discord.PermissionOverwrite = discord.PermissionOverwrite()
        overwrite.update(add_reactions=False)
        await channel.set_permissions(role, overwrite=overwrite)
        bot_members = [member for member in guild.members if member.bot and member.id == bot.user.id]
        overwrite.update(add_reactions=True)
        for bot_member in bot_members:
            await channel.set_permissions(bot_member, overwrite=overwrite)
    except discord.errors.Forbidden:
        raise PermissionsException("Koala needs the manage_roles permission to create a RFR in this channel.")
