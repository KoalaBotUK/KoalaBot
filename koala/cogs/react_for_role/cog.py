#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

Author: Anan Venkatesh
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
from io import BytesIO
from typing import *

import aiohttp
import discord
import emoji
from discord import app_commands, Message
from discord.ext import commands

import koalabot
from koala.colours import KOALA_GREEN
from koala.db import insert_extension
from koala.utils import wait_for_message
# Own modules
from . import core
from .db import get_rfr_message, get_rfr_message_emoji_roles, get_guild_rfr_messages, get_guild_rfr_roles, \
    get_guild_rfr_required_roles
from .dto import ReactMessage
from .log import logger
from .ui import ReactForRoleCreate, RfrEditMenu, RfrEditMenuOptions, RfrRemoveRoles


def rfr_is_enabled(ctx):
    """
    A command used to check if the guild has enabled rfr
    e.g. @commands.check(rfr_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(ctx, "ReactForRole")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == koalabot.TEST_USER and koalabot.is_dpytest)


@app_commands.default_permissions(administrator=True)
class ReactForRole(commands.GroupCog, group_name="rfr", group_description="React For Role message for role assignment"):
    """
    A discord.py cog pertaining to a React for Role system to allow for automation in getting roles.
    """
    edit_group = app_commands.Group(name="edit", description="Edit an existing RFR message")

    def __init__(self, bot):
        self.bot = bot
        insert_extension("ReactForRole", 0, True, True)

    @commands.check(koalabot.is_guild_channel)
    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @commands.group(name="rfr", aliases=["reactForRole", "react_for_role"])
    async def react_for_role_group(self, ctx: commands.Context):
        """
        Group of commands for React for Role (rfr) functionality.
        :param ctx: Context of the command
        :return:
        """
        return

    @staticmethod
    async def get_image_from_url(ctx: discord.ext.commands.Context, url: str) -> str:
        """
        Gets a workable image URL that was sent/handled without a file attachment in disc, but as a raw URL in msg content. Works by sending the image in the same context, then getting that attachment
        :param ctx: Context of the original message
        :param url: Original raw URL
        :return: URL of attachment to use in a method call
        """

        async def file_type_from_hdr(resp: aiohttp.ClientResponse):
            """
            Gets a file extension based only on the Content-Type MIME type header of the HTTP GET request sent.
            :param resp: Original HTTP response
            :return: file ext or empty string if not compatible as discord image
            """
            content_type: str = resp.content_type
            if content_type == 'image/png':
                return "png"
            elif content_type == 'image/jpeg':
                return "jpg"
            elif content_type == 'image/gif':
                return "gif"
            else:
                return None

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(
                        "RFR: HTTP error Access code " + str(response.status) + " when attempting GET on " + url)
                    raise aiohttp.ClientError(
                        "HTTP error Access code " + str(response.status) + " when attempting GET on " + url)
                image_bytes = await response.read()
                data = BytesIO(image_bytes)
                ftype: str = await file_type_from_hdr(response)
                if not ftype:
                    logger.error(
                        "RFR: Couldn't verify image file type from " + url + " due to missing/different Content-Type header")
                    raise commands.BadArgument("Couldn't get an image from the message you sent.")
                msg: discord.Message = await ctx.send(file=discord.File(data, f"thumbnail.{ftype}"))
                try:
                    img = msg.attachments[0].url
                    await msg.delete()
                    return img
                except Exception as e:
                    logger.error("RFR " + str(e))
                    raise e

    @staticmethod
    def attachment_img_content_type(mime: Optional[str]):
        if not mime:
            return False
        else:
            return mime.startswith("image/")

    @app_commands.command(name="create", description="Creates a new ReactForRole message")
    async def rfr_create_message(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        Creates a new rfr message in a channel of user's choice. User is prompted for (in this order)
        channel ID/name/mention, message title, message description. Default title and description exist, which are
        "React for Role" and "Roles below!" respectively. User requires admin perms to use.

        Note: The channel you specify will have its permissions edited to make it such that the @ everyone role
        is unable to add new reactions to messages, they can only reaction with existing ones. Please keep this in
        mind, or setup another channel entirely for this.
        :param interaction: Interaction of the command
        :param channel: channel for creating message
        :return:
        """
        await interaction.response.send_modal(ReactForRoleCreate(self.bot, channel))
        # TODO - Get this working, for some reason we get 403 currently
        # await core.setup_rfr_reaction_permissions(ctx.guild, channel, self.bot)
        # await self.overwrite_channel_add_reaction_perms(interaction.guild, channel)

    @app_commands.command(name="delete", description="Deletes an existing ReactForRole message")
    async def rfr_delete_message(self, interaction: discord.Interaction, channel: discord.TextChannel, message_id: int):
        """
        Deletes an existing rfr message.
        :param interaction: Interaction of the command.
        :param channel: Channel of RFR message.
        :param message_id: Message ID of RFR message.
        :return:
        """
        await core.delete_rfr_message(self.bot, message_id, channel.guild.id, channel.id)
        await interaction.response.send_message("ReactForRole Message deleted")

    @app_commands.command(name="edit", description="Edit an existing ReactForRole message")
    async def rfr_edit_message(self, interaction: discord.Interaction, channel: discord.TextChannel, message_id: str):
        existing_rfr: ReactMessage = await core.get_rfr_message_dto(self.bot, message_id, channel.guild.id, channel.id)
        view = RfrEditMenu(interaction)
        await interaction.response.send_message("", view=view, ephemeral=True)
        await view.wait()
        if view.value == RfrEditMenuOptions.ALTER_CONFIG:
            alter_modal = ReactForRoleCreate(self.bot, channel, existing_rfr.title, existing_rfr.description,
                                             existing_rfr.colour, existing_rfr.thumbnail, message_id)
            await view.interaction.response.send_modal(alter_modal)
            await alter_modal.wait()
            # await alter_modal.wait()
        elif view.value == RfrEditMenuOptions.ADD_ROLES:
            msg = await channel.fetch_message(message_id)
            remaining_slots = 20 - core.get_number_of_embed_fields(core.get_embed_from_message(msg))

            await view.interaction.response.send_message(
                "Okay. Can I get the roles and emojis you want added to the message in a list with format: \n<emoji>,"
                " <role>\n<emoji>, <role>\n<emoji>, <role>\netc. You can get a new line by using SHIFT + ENTER. \n\n"
                f"Please note however that you've only got {remaining_slots} emoji-role combinations you can enter. I'll "
                f"therefore only take the first {remaining_slots} you do. I'll wait for 3 minutes.", ephemeral=True)

            input_role_emojis = (await wait_for_message(self.bot, interaction, 180))[0].content
            emoji_role_list = await self.parse_emoji_and_role_input_str_interaction(self.bot, interaction,
                                                                                    input_role_emojis, remaining_slots)
            duplicate_roles_found, duplicate_emojis_found, edited_msg = await core.rfr_add_emoji_role(interaction.guild,
                                                                                                      channel,
                                                                                                      msg,
                                                                                                      emoji_role_list)
            if duplicate_emojis_found or duplicate_roles_found:
                await view.interaction.edit_original_response(
                    content="Found duplicate emoji in the message, I'm not accepting it.")
            await view.interaction.edit_original_response(
                content="Okay, you should see the message with its new emojis now.")
        elif view.value == RfrEditMenuOptions.REMOVE_ROLES:
            remove_role_view = RfrRemoveRoles(channel.guild, existing_rfr.roles)
            await view.interaction.response.send_message(content="Select React Roles to remove",
                                                         view=remove_role_view, ephemeral=True)
            await remove_role_view.wait()
            if remove_role_view.value == 1:
                msg = await channel.fetch_message(message_id)
                await core.rfr_remove_emojis_roles(self.bot, channel.guild, msg,
                                                   get_rfr_message(channel.guild.id, channel.id, message_id),
                                                   remove_role_view.role_select.values)
                await view.interaction.edit_original_response(
                    content="Okay, Roles are removed")
        else:
            await interaction.edit_original_response(content="Timed out.", view=None)
            return
        await interaction.delete_original_response()

    @react_for_role_group.group(name="edit", pass_context=True)
    async def edit_group(self, ctx: commands.Context):
        return

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="description", aliases=["desc"])
    async def rfr_edit_description(self, ctx: commands.Context):
        """
        Edit the description of an existing rfr message. User is prompted for rfr message channel ID/name/mention,
        rfr message ID/URL, new description, Y/N confirmation. User needs admin perms to use.
        :param ctx: Context of the command
        :return:
        """
        await ctx.send("Okay, this will edit the description of an existing react for role message. I'll need some "
                       "details first though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        embed = core.get_embed_from_message(msg)
        await ctx.send(f"Your current description is {embed.description}. Please enter your new description.")
        desc = await self.prompt_for_input(ctx, "description")
        if desc != "":
            await ctx.send(f"Your new description would be {desc}. Please confirm that you'd like this change.")
            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await core.rfr_edit(msg, description=desc)
            else:
                await ctx.send("Okay, cancelling command.")
        else:
            await ctx.send("Okay, cancelling command.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="title")
    async def rfr_edit_title(self, ctx: commands.Context):
        """
        Edit the title of an existing rfr message. User is prompted for rfr message channel ID/name/mention,
        rfr message ID/URL, new title, Y/N confirmation. User needs admin perms to use.
        :param ctx: Context of the command
        :return:
        """
        await ctx.send("Okay, this will edit the title of an existing react for role message. I'll need some details "
                       "first though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        embed = core.get_embed_from_message(msg)
        await ctx.send(f"Your current title is {embed.title}. Please enter your new title.")
        title = await self.prompt_for_input(ctx, "title")
        if title != "":
            await ctx.send(f"Your new title would be {title}. Please confirm that you'd like this change.")
            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await core.rfr_edit(msg, title=title)
            else:
                await ctx.send("Okay, cancelling command.")
        else:
            await ctx.send("Okay, cancelling command.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="thumbnail", aliases=["image", "picture"])
    async def rfr_edit_thumbnail(self, ctx: commands.Context):
        """
        Edit the thumbnail of an existing rfr message. User is prompted for rfr message channel ID/name/mention, rfr
        message ID/URL, new thumbnail, Y/N confirmation. User needs admin perms
        :param ctx: Context of the command
        :return:
        """
        await ctx.send("Okay, this will edit the thumbnail of a react for role message. I'll need some details first "
                       "though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        embed = core.get_embed_from_message(msg)
        if not embed:
            logger.error(
                f"RFR: Can't find embed for message id {msg.id}, channel {channel.id}, guild id {ctx.guild.id}.")
        await ctx.send(f"Your current image here is {embed.thumbnail.url}")
        image = await self.prompt_for_input(ctx, "image you'd like to use as a thumbnail")
        if not image or image == "":
            await ctx.send("Okay, cancelling command.")
        if isinstance(image, discord.Attachment) and self.attachment_img_content_type(image.content_type):
            # correct type
            if not image.url:
                logger.error(f"Attachment url not found, details : {image}")
                raise commands.BadArgument("Couldn't get an image from the message you sent.")
            else:
                await core.rfr_edit(msg, thumbnail_url=str(image.url))
                await ctx.send("Okay, set the thumbnail of the thumbnail to your desired image. This will error if you "
                               "delete the message you sent with the image, so make sure you don't.")
        elif isinstance(image, str):
            # no attachment in message, just a raw URL in content
            img_url = await self.get_image_from_url(ctx, image)
            await core.rfr_edit(msg, thumbnail_url=img_url)
            await ctx.send("Okay, set the thumbnail of the thumbnail to your desired image.")
        else:
            raise commands.BadArgument("Couldn't get an image from the message you sent.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="inline")
    async def rfr_edit_inline(self, ctx: commands.Context):
        """
        Edit the inline property of embed fields in rfr embeds. Can edit all rfr messages in a server or a specific one.
        User is prompted for whether they'd like inline fields or not, as well as details of the specific message if
        that option is selected. User requires admin perms
        :param ctx: Context of the command
        :return:
        """
        await ctx.send("Okay, this will change how your embeds look. By default fields are not inline. However, you can"
                       " choose to change this for a specific message or all rfr messages on the server. To do this, I'"
                       "ll need some information though. Can you say if you want a specific message edited, or all mess"
                       "ages on the server?")
        input = await self.prompt_for_input(ctx, "all or specific")
        if not isinstance(input, str) or not input:
            await ctx.send("Okay, cancelling command")
        else:
            input_comm = input.lstrip().rstrip().lower()
            if input_comm not in ["all", "specific"]:
                await ctx.send("Okay, cancelling command.")
            elif input_comm == "all":
                await ctx.send(
                    "Okay, do you want all rfr messages in this server to have inline fields or not? Y for yes, "
                    "N for no.")
                change_all = await self.prompt_for_input(ctx, "Y/N")
                if not change_all or change_all.rstrip().lstrip().upper() not in ["Y", "N"]:
                    await ctx.send("Okay, cancelling command")
                    return
                change_all = change_all.rstrip().lstrip().upper()
                if change_all not in ["Y", "N"]:
                    await ctx.send("Invalid input for Y/N. Okay, cancelling command")
                    return
                else:
                    await ctx.send(
                        "Keep in mind that this process may take a while if you have a lot of RFR messages on your "
                        "server.")
                    await core.use_inline_rfr_all(ctx.guild)
                    await ctx.send("Okay, the process should be finished now. Please check.")
            elif input_comm.lstrip().rstrip().lower() == "specific":
                # try and get specific message
                await ctx.send("Okay, I'll need the information about the specific rfr message.")
                msg, channel = await self.get_rfr_message_from_prompts(ctx)
                embed: discord.Embed = core.get_embed_from_message(msg)
                if not embed:
                    await ctx.send("Couldn't get embed, is this an RFR message?")
                else:
                    await ctx.send("Okay, please say Y if you want inline fields, or N if you don't.")
                    yes_no = await self.prompt_for_input(ctx, "Y/N")
                    if not yes_no or yes_no.lstrip().rstrip().upper() not in ["Y", "N"]:
                        await ctx.send("Invalid input, cancelling command.")
                        return
                    yes_no = yes_no.lstrip().rstrip().upper()
                    if yes_no not in ["Y", "N"]:
                        await ctx.send("Invalid input, cancelling command")
                    else:
                        await ctx.send("Okay, I'll change it as requested.")
                        await core.use_inline_rfr_specific(msg)
                        await ctx.send("Okay, should be done. Please check.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="fixEmbed")
    async def rfr_fix_embed(self, ctx: commands.Context):
        """
        Cosmetic fix method if the bot ever has a moment and doesn't react with the correct emojis/has duplicates.
        """
        msg, chnl = await self.get_rfr_message_from_prompts(ctx)
        await core.setup_rfr_reaction_permissions(chnl.guild, chnl, self.bot)
        emb = core.get_embed_from_message(msg)
        reacts: List[Union[discord.PartialEmoji, discord.Emoji, str]] = [x.emoji for x in msg.reactions]
        if not emb:
            logger.error(
                f"RFR: Can't find embed for message id {msg.id}, channel {chnl.id}, guild id {ctx.guild.id}.")
        else:
            er_id, _, _, _ = get_rfr_message(ctx.guild.id, chnl.id, msg.id)
            if not er_id:
                logger.error(
                    f"RFR: Can't find rfr message with {msg.id}, channel {chnl.id}, guild id {ctx.guild.id}. DB ER_ID : {er_id}")
            else:
                rfr_er = get_rfr_message_emoji_roles(er_id)
                if not rfr_er:
                    logger.error(
                        f"RFR: Can't retrieve RFR message (ER_ID: {er_id})'s emoji role combinations.")
                else:
                    combos = ""
                    for er in rfr_er:
                        combos += er[1] + ", " + str(er[2]) + "\n"
                    er_list = await self.parse_emoji_and_role_input_str(ctx, combos, 20)
                    embed: discord.Embed = discord.Embed(title=emb.title, description=emb.description,
                                                         colour=KOALA_GREEN)
                    embed.set_footer(text=emb.footer)
                    embed.set_thumbnail(url=emb.thumbnail.url)
                    emb.set_image(url=emb.image.url)
                    for e in reacts:
                        if e not in [x for x, _ in er_list]:
                            await msg.clear_reaction(e)
                    for e, r in er_list:
                        embed.add_field(name=str(e), value=r.mention, inline=False)
                        if e not in reacts:
                            await msg.add_reaction(e)
                    await msg.edit(embed=embed)
                    await ctx.send("Tried fixing the message, please check that it's fixed.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="addRoles")
    async def rfr_add_roles_to_msg(self, ctx: commands.Context):
        """
        Adds roles to an existing rfr message. User is prompted for rfr message channel ID/name/mention, rfr message ID/
        URL, emoji-role combos. Emoji-role combinations are to be given in
        \\\n\"<emoji>, <role>\"
        \\\n\"<emoji>, <role>\"
        format. <role> can be the role ID, name or mention. `emoji` can be a custom emoji from the server, or a standard
        unicode emoji. \\\nUser needs admin perms to use.
        :param ctx: Context of the command.
        :return:
        """

        await ctx.send(
            "Okay. This will add roles to an already created react for role message. I'll need some details first "
            "though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        rfr_msg_row = get_rfr_message(ctx.guild.id, channel.id, msg.id)

        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        await ctx.send("Okay, found the message you want to add to.")
        remaining_slots = 20 - core.get_number_of_embed_fields(core.get_embed_from_message(msg))

        if remaining_slots == 0:
            await ctx.send(
                "Unfortunately due to discord limitations that message cannot have any more reactions. If you want I "
                "can create another message in the same channel though. Shall I do that?")

            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await ctx.send(
                    "Okay, I'll continue then. The new message will have the same title and description as the "
                    "old one.")
                old_embed = core.get_embed_from_message(msg)
                rfr_msg_id = (await core.create_rfr_message(self.bot, ctx.guild.id, channel.id,
                                                            title=old_embed.title, description=old_embed.description,
                                                            colour=KOALA_GREEN)).message_id
                await ctx.send(f"Okay, the new message has ID {rfr_msg_id} and is in {msg.channel.mention}.")
            else:
                await ctx.send("Okay, I'll stop the command then.")
                return

        await ctx.send(
            "Okay. Can I get the roles and emojis you want added to the message in a list with format: \n<emoji>,"
            " <role>\n<emoji>, <role>\n<emoji>, <role>\netc. You can get a new line by using SHIFT + ENTER.")
        await ctx.send(
            f"Please note however that you've only got {remaining_slots} emoji-role combinations you can enter. I'll "
            f"therefore only take the first {remaining_slots} you do. I'll wait for 3 minutes.")

        input_role_emojis = (await wait_for_message(self.bot, ctx, 180))[0].content
        emoji_role_list = await self.parse_emoji_and_role_input_str(ctx, input_role_emojis, remaining_slots)
        duplicateRolesFound, duplicateEmojisFound, edited_msg = await core.rfr_add_emoji_role(ctx.guild, channel,
                                                                                              msg, emoji_role_list)
        if (duplicateEmojisFound): await ctx.send("Found duplicate emoji in the message, I'm not accepting it.")
        if (duplicateRolesFound): await ctx.send("Found duplicate roles in the message, I'm not accepting it.")
        await ctx.send("Okay, you should see the message with its new emojis now.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="removeRoles")
    async def rfr_remove_roles_from_msg(self, ctx: commands.Context):
        """
        Removes roles from an existing rfr message. User is prompted for rfr message channel ID/name/mention, rfr message
        ID/URL, emojis/roles to remove. User can specify either the emoji or the role for any emoji-role combination to
        remove it, but it needs to be specified in the format below.
        \\\n\"<emoji>/<role>\"
        \\\n\"<emoji>/<role>\"
        <role> can be the role ID, name or mention. emoji can be a custom emoji from the server, or a standard
        unicode emoji. \\\nUser needs admin perms to use.
        :param ctx: Context of the command.
        :return:
        """
        await ctx.send(
            "Okay, this will remove roles from an already existing react for role message. I'll need some details first"
            " though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        rfr_msg_row = get_rfr_message(ctx.guild.id, channel.id, msg.id)

        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        await ctx.send("Okay, found the message you want to remove roles from.")
        remaining_slots = core.get_number_of_embed_fields(core.get_embed_from_message(msg))

        if remaining_slots == 0:
            await ctx.send(
                "Okay, it looks like you've already gotten rid of all roles from this message. Would you like me to del"
                "ete the message too?")

            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await ctx.send("Okay, deleting that message and removing it from the database.")
                await core.delete_rfr_message(self.bot, msg.id, ctx.guild.id, channel.id)
                await ctx.send("Okay, deleted that react for role message. Have a nice day.")
                return
            else:
                await ctx.send("Okay, I'll stop the command then.")
                return
        else:
            await ctx.send(
                "Okay, I'll take the info of the roles/emojis you want to remove now. Just enter it in a message "
                "separated by new lines (SHIFT+ENTER). You can enter either the emojis used or the roles' ID/mention/"
                "name, for each one.")

            input_emoji_roles = (await wait_for_message(self.bot, ctx, 120))[0].content
            wanted_removals = await self.parse_emoji_or_roles_input_str(ctx, input_emoji_roles)

            new_embed, errors = core.rfr_remove_emojis_roles(self.bot, ctx.guild, msg, rfr_msg_row, wanted_removals)
            for e in errors:
                await ctx.send(e)

            if core.get_number_of_embed_fields(new_embed) == 0:
                await ctx.send("I see you've removed all emoji-role combinations from this react for role message. "
                               "Would you like to delete this message?")

                if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                    await ctx.send("Okay, I'll delete the message then.")
                    await core.delete_rfr_message(self.bot, msg.id, ctx.guild.id, channel.id)
                    return

            await ctx.send("Okay, I've removed those options from the react for role message.")

    @commands.Cog.listener()
    @commands.check(koalabot.is_guild_channel)
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Event listener for adding a reaction. Doesn't need message to be in loaded cache.
        Gives the user a role if they can get it, if not strips all their roles and removes their reacts.
        :param payload: RawReactionActionEvent that happened
        :return:
        """
        if payload.guild_id is not None:
            if not payload.member.bot:
                rfr_message = get_rfr_message(payload.guild_id, payload.channel_id,
                                              payload.message_id)
                if not rfr_message:
                    return

                member_role = await self.get_role_member_info(payload.emoji, payload.guild_id,
                                                              payload.channel_id,
                                                              payload.message_id, payload.user_id)
                if not member_role:
                    # Remove the reaction
                    guild: discord.Guild = self.bot.get_guild(payload.guild_id)
                    channel: discord.TextChannel = guild.get_channel(payload.channel_id)
                    msg: discord.Message = await channel.fetch_message(payload.message_id)
                    await msg.clear_reaction(payload.emoji)
                else:
                    if self.can_have_rfr_role(member_role[0]):
                        await member_role[0].add_roles(member_role[1])
                    else:
                        # Remove all rfr roles from member
                        role_ids = get_guild_rfr_roles(payload.guild_id)
                        roles: List[discord.Role] = []
                        for role_id in role_ids:
                            role = discord.utils.get(member_role[0].guild.roles, id=role_id)
                            if not role:
                                continue
                            roles.append(role)
                        for role_to_remove in roles:
                            await member_role[0].remove_roles(role_to_remove)
                        # Remove members' reaction from all rfr messages in guild
                        guild_rfr_messages = get_guild_rfr_messages(payload.guild_id)
                        if not guild_rfr_messages:
                            logger.error(
                                f"ReactForRole: Guild RFR messages is empty on raw reaction add. Please check"
                                f" guild ID {payload.guild_id}")

                        else:
                            for guild_rfr_message in guild_rfr_messages:
                                guild: discord.Guild = member_role[0].guild
                                channel: discord.TextChannel = guild.get_channel(guild_rfr_message[1])
                                msg: discord.Message = await channel.fetch_message(guild_rfr_message[2])
                                for x in msg.reactions:
                                    await x.remove(payload.member)

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command("addRequiredRole")
    async def rfr_add_guild_required_role(self, ctx: commands.Context, role: discord.Role):
        """
        Adds a role to perms to use rfr functionality in a server, so you can specify that you need, e.g. "@Student" to
        be able to use rfr functionality in the server. It's server-wide permissions handling however. By default anyone
        can use rfr functionality in the server. User needs to have admin perms to use.
        :param ctx: Context of the command
        :param role: Role ID/name/mention
        :return:
        """
        try:
            core.add_guild_rfr_required_role(ctx.guild, role.id)
            await ctx.send(f"Okay, I'll add {role.name} to the list of roles required for RFR usage on the server.")
        except (commands.CommandError, commands.BadArgument):
            await ctx.send("Found an issue with your provided argument, couldn't get an actual role. Please try again.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command("removeRequiredRole")
    async def rfr_remove_guild_required_role(self, ctx: commands.Context, role: discord.Role):
        """
        Removes a role from perms for use of rfr functionality in a server, so you can specify that you need, e.g.
        "@Student" to be able to use rfr functionality in the server. It's server-wide permissions handling however. By
        default anyone can use rfr functionality in the server. User needs to have admin perms to use.
        :param ctx: Context of the command
        :param role: Role ID/name/mention
        :return:
        """
        try:
            core.remove_guild_rfr_required_role(ctx.guild, role.id)
            await ctx.send(
                f"Okay, I'll remove {role.name} from the list of roles required for RFR usage on the server.")
        except (commands.CommandError, commands.BadArgument):
            await ctx.send("Found an issue with your provided argument, couldn't get an actual role. Please try again.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command("listRequiredRoles")
    async def rfr_list_guild_required_roles(self, ctx: commands.Context):
        """
        Lists the server-specific role permissions for using rfr functionality. If list is empty, any role can use rfr
        functionality.
        :param ctx: Context of the command.
        :return:
        """
        role_ids = core.rfr_list_guild_required_roles(ctx.guild).role_ids
        msg_str = "You will need one of these roles to react to rfr messages on this server:\n"
        for role_id in role_ids:

            role: discord.Role = discord.utils.get(ctx.guild.roles, id=role_id)
            if not role:
                logger.error(f"ReactForRole: Couldn't find role {role_id} in guild {ctx.guild.id}. Please "
                             f"check.")
            else:
                msg_str += f"{role.mention}\n"
        if msg_str == "You will need one of these roles to react to rfr messages on this server:\n":
            msg_str = "Anyone can react to rfr messages on this server."
        await ctx.send(msg_str)

    @commands.Cog.listener()
    @commands.check(koalabot.is_guild_channel)
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Event listener for removing a reaction. Doesn't need message to be in loaded cache. Removes the role from the
        user if they have it, else does nothing.
        :param payload: RawReactionActionEvent that happened.
        :return:
        """

        if payload.guild_id is not None:
            rfr_message = get_rfr_message(payload.guild_id, payload.channel_id,
                                          payload.message_id)
            if not rfr_message:
                return
            member_role = await self.get_role_member_info(payload.emoji, payload.guild_id,
                                                          payload.channel_id,
                                                          payload.message_id, payload.user_id)
            if not member_role or member_role[0].bot:
                return
            await member_role[0].remove_roles(member_role[1])

    def can_have_rfr_role(self, member: discord.Member) -> bool:
        """
        check for rfr required roles, taking a member as argument
        :param member: Member to check rfr perms for
        :return: True if member has one of the required roles, or if there are no required roles. False otherwise
        """
        required_roles: List[int] = get_guild_rfr_required_roles(member.guild.id)
        if not required_roles or len(required_roles) == 0:
            return True
        return any(x in required_roles for x in [y.id for y in member.roles])

    async def get_rfr_message_from_prompts(self, ctx: commands.Context) -> Tuple[discord.Message, discord.TextChannel]:
        """
        Gets an rfr message from prompting user, basically just calls prompt_for_input multiple times and gets value from
        database based on input.
        :param ctx: Context of the command this function is called in
        :return: 2-Tuple of the message (if there is one, else None), and channel (if there is no message, else None).
        """
        channel_raw = await self.prompt_for_input(ctx, "Channel name, mention or ID")
        channel = None if (channel_raw == "") else await commands.TextChannelConverter().convert(ctx, channel_raw)
        if not channel:
            raise commands.CommandError("Invalid channel given.")
        msg_id_raw = await self.prompt_for_input(ctx, "react for role message ID")
        msg_id = None if (msg_id_raw == "") else int(msg_id_raw)
        if not msg_id:
            raise commands.CommandError("Invalid Message ID given.")
        msg = await channel.fetch_message(msg_id)
        if not msg:
            raise commands.CommandError("Invalid Message ID given.")
        rfr_msg_row = get_rfr_message(ctx.guild.id, channel.id, msg_id)
        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        return msg, channel

    async def get_role_member_info(self, emoji_reacted: discord.PartialEmoji, guild_id: int,
                                   channel_id: int, message_id: int, user_id: int) -> Optional[
        Tuple[discord.Member, discord.Role]]:
        """
        Gets the role that should be added/removed to/from a Member on reacting to a known RFR message, and works out
        which Member reacted.
        :param emoji_reacted: Emoji of the raw reaction payload
        :param emoji_role_id: DB key identifying specific RFR message in a Guild
        :param guild_id: ID of the guild this event occurred in
        :param channel_id: ID of the channel that the message was in
        :param message_id: ID of the message that was reacted to
        :param user_id: ID of the user who reacted
        :return: Optional 2-Tuple (member, role) where member is the Member that reacted, and Role is the role that
        should be given/taken away. If a role or member couldn't be found, returns None instead.
        """

        guild: discord.Guild = self.bot.get_guild(guild_id)
        member: discord.Member = discord.utils.get(guild.members, id=user_id)
        if not member:
            return
        channel: discord.TextChannel = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            return
        message: discord.Message = await channel.fetch_message(message_id)
        if not message:
            return
        embed: discord.Embed = core.get_embed_from_message(message)

        if emoji_reacted.is_unicode_emoji():
            rep = emoji.emojize(emoji_reacted.name)
            if not rep:
                rep = emoji.emojize(emoji_reacted.name, use_aliases=True)

            field = await self.get_field_by_emoji(embed, rep)
            if not field:
                return
            role_str: str = field
            if not role_str:
                return
            role: discord.Role = discord.utils.get(guild.roles, mention=role_str.lstrip().rstrip())
            if not role:
                return
        elif emoji_reacted.is_custom_emoji():
            rep = str(emoji_reacted)
            field = await self.get_field_by_emoji(embed, rep)
            if not field:
                # Look for animated version
                field = await self.get_field_by_emoji(embed, rep[0] + "a" + rep[1:])
            if not field:
                return
            role_str = field
            role: discord.Role = discord.utils.get(guild.roles, mention=role_str.lstrip().rstrip())
        else:
            logger.error(
                f"ReactForRole: Database error, guild {guild_id} has no entry in rfr database for message_id "
                f"{message_id} in channel_id {channel_id}. Please check this.")
            return
        return member, role

    async def parse_emoji_and_role_input_str_interaction(self, bot, interaction: discord.Interaction, input_str: str,
                                                         remaining_slots: int) -> List[
        Tuple[Union[discord.Emoji, str], discord.Role]]:
        """
        Parses input for the "k!rfr edit addRoles" commmand, in the
        \n"<emoji>, <role>\n
        <emoji>, <role>"
        format.
        :param ctx: context of the command that called this
        :param input_str: input message content
        :param remaining_slots: remaining slots left on the rfr embed referred to
        :return: List of Emoji-Role pairs parsed from the input message.
        """
        rows = input_str.splitlines()

        arr = []
        for row in rows:
            emoji_role = row.split(',')
            # print(emoji_role)
            if (len(emoji_role) < 2):
                continue
            if len(emoji_role) > 2:
                raise commands.BadArgument("Too many/little categories/etc on one line.")
            emoji, err = await core.get_first_emoji_from_str(bot, interaction.guild, emoji_role[0].strip())

            if not emoji:
                await interaction.edit_original_response(
                    content=f"Yeah, didn't find emoji for `{emoji_role[0]}` - {err}")
                continue

            role = await commands.RoleConverter().convert(interaction, emoji_role[1].lstrip().rstrip())
            arr.append((emoji, role))
            if len(arr) == remaining_slots:
                return arr
        return arr

    async def parse_emoji_and_role_input_str(self, ctx: commands.Context, input_str: str, remaining_slots: int) -> List[
        Tuple[Union[discord.Emoji, str], discord.Role]]:
        """
        Parses input for the "k!rfr edit addRoles" commmand, in the
        \n"<emoji>, <role>\n
        <emoji>, <role>"
        format.
        :param ctx: context of the command that called this
        :param input_str: input message content
        :param remaining_slots: remaining slots left on the rfr embed referred to
        :return: List of Emoji-Role pairs parsed from the input message.
        """
        rows = input_str.splitlines()

        arr = []
        for row in rows:
            emoji_role = row.split(',')
            # print(emoji_role)
            if (len(emoji_role) < 2):
                continue
            if len(emoji_role) > 2:
                raise commands.BadArgument("Too many/little categories/etc on one line.")
            emoji, err = await core.get_first_emoji_from_str(ctx.bot, ctx.guild, emoji_role[0].strip())

            if not emoji:
                await ctx.send(f"Yeah, didn't find emoji for `{emoji_role[0]}` - {err}")
                continue

            role = await commands.RoleConverter().convert(ctx, emoji_role[1].lstrip().rstrip())
            arr.append((emoji, role))
            if len(arr) == remaining_slots:
                return arr
        return arr

    async def parse_emoji_or_roles_input_str(self, ctx: commands.Context, input_str: str) -> List[
        Union[discord.Emoji, str, discord.Role]]:
        """
        Parses input prompt for the "k!rfr edit removeRoles" command, to get a list of roles and emoji as the output.
        Input format is
        \n"<emoji>/<role>\n
        <emoji>/<role>"
        <role> can be the role ID, name or mention. emoji can be a custom emoji from the server, or a standard
        unicode emoji.
        :param ctx: Context of the command that called this
        :param input_str: Input message content
        :return: List of roles & emojis given in the input string.
        """
        rows = input_str.splitlines()
        arr = []
        for row in rows:
            # Try and match it to an raw_emoji first
            raw_emoji, err = await core.get_first_emoji_from_str(self.bot, ctx.guild, row.strip())
            if err:
                await ctx.send(err)
            if not raw_emoji:
                role = await commands.RoleConverter().convert(ctx, row.strip())
                if not role:
                    raise commands.BadArgument("Couldn't convert to a role or emoji.")
                else:
                    arr.append(role)
            else:
                arr.append(raw_emoji)
        return arr

    async def prompt_for_input(self, ctx: commands.Context, input_type: str) -> Union[discord.Attachment, str]:
        """
        Prompts a user for input in the form of a message. Has a forced timer of 60 seconds, because it basically just
        deals with the rfr specific stuff. Returns whatever was input, or cancels the calling command
        :param ctx: Context of the command that calls this
        :param input_type: Name of whatever info is needed from a user, just so that the message looks nice/clear
        :return: User's response's content
        """
        await ctx.send(f"Please enter {input_type} so I can progress further. I'll wait 60 seconds, don't worry.")
        msg, channel = await wait_for_message(self.bot, ctx)
        if not msg:
            await channel.send("Okay, I'll cancel the command.")
            return ""
        elif len(msg.attachments) > 0:
            return msg.attachments[0]
        else:
            return msg.content

    async def is_user_alive(self, ctx: commands.Context):
        """
        Prompts user for message to check if they're alive. Any message will do. We hope they're alive anyways.
        :param ctx: Context of the command that calls this
        :return: True if message received, False otherwise.
        """
        msg = await wait_for_message(self.bot, ctx, 10)
        if not msg[0]:
            return False
        return True

    async def get_field_by_emoji(self, embed: discord.Embed, emoji: Optional[str]):
        """
        Get the specific field value of an rfr embed by the string representation of the emoji in the field name

        :param embed: RFR Embed to check
        :param emoji: Emoji required
        :return: If a field exists such that its name is :emoji:, then that field's value. Else None
        """
        if not emoji:
            return
        else:
            fields = embed.fields
            field = discord.utils.get(fields, name=emoji)
            if not field:
                return
            return field.value


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    await bot.add_cog(ReactForRole(bot))
