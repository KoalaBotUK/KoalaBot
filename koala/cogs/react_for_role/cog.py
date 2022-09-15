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
from discord.ext import commands

# Own modules
import koalabot
from koala.colours import KOALA_GREEN
from koala.utils import wait_for_message
from koala.db import insert_extension
from .db import ReactForRoleDBManager
from .exception import ReactionException, ReactionErrorCode
from .log import logger
from .utils import CUSTOM_EMOJI_REGEXP, UNICODE_EMOJI_REGEXP


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


class ReactForRole(commands.Cog):
    """
    A discord.py cog pertaining to a React for Role system to allow for automation in getting roles.
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot
        insert_extension("ReactForRole", 0, True, True)
        self.rfr_database_manager = ReactForRoleDBManager()

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

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command(name="create", aliases=["createMsg", "createMessage"])
    async def rfr_create_message(self, ctx: commands.Context):
        """
        Creates a new rfr message in a channel of user's choice. User is prompted for (in this order)
        channel ID/name/mention, message title, message description. Default title and description exist, which are
        "React for Role" and "Roles below!" respectively. User requires admin perms to use.
        :param ctx: Context of the command
        :return:
        """
        await ctx.send(
            "Okay, this will create a new react for role message in a channel of your choice."
            "\nNote: The channel you specify will have its permissions edited to make it such that the @ everyone role "
            "is unable to add new reactions to messages, they can only reaction with existing ones. Please keep this in"
            " mind, or setup another channel entirely for this.")
        channel_raw = await self.prompt_for_input(ctx, "channel ID, name or mention")
        channel = None if (channel_raw == "") else await commands.TextChannelConverter().convert(ctx, channel_raw)
        if not channel:
            await ctx.send("Sorry, you didn't specify a valid channel ID, mention or name. Please restart the command.")
        else:
            del_msg = await channel.send(f"This should be a thing sent in the right channel.")
            await ctx.send(
                "Okay, what would you like the title of the react for role message to be? Please enter within 60"
                " seconds.")
            x = await wait_for_message(self.bot, ctx)
            msg: discord.Message = x[0]
            if not x[0]:
                await ctx.send(
                    "Okay, didn't receive a title. Do you actually want to continue? Send anything to confirm this.")
                if not await self.is_user_alive(ctx):
                    await ctx.send("Okay, didn't receive any confirmation. Cancelling command. Please restart.")
                    await del_msg.delete()
                    return
                else:
                    title: str = "React for Role"
                    await ctx.send(
                        "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr edit"
                        " commands.")
            else:
                title: str = msg.content
            await ctx.send(
                f"Okay, the title of the message will be \"{title}\". What do you want the description to be? "
                f"I'll wait 60 seconds, don't worry")
            y = await wait_for_message(self.bot, ctx)
            msg: discord.Message = y[0]
            if not y[0]:
                await ctx.send(
                    "Okay, didn't receive a description. Do you actually want to continue? Send anything to confirm this.")
                if not await self.is_user_alive(ctx):
                    await ctx.send("Okay, didn't receive any confirmation. Cancelling command. Please restart.")
                    await del_msg.delete()
                    return
                else:
                    desc: str = "Roles below!"
                    await ctx.send(
                        "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr "
                        "edit command.")
            else:
                desc: str = msg.content
            await ctx.send(f"Okay, the description of the message will be \"{desc}\".\n Okay, "
                           f"I'll create the react for role message now.")
            embed: discord.Embed = discord.Embed(title=title, description=desc, colour=KOALA_GREEN)
            embed.set_footer(text="ReactForRole")
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png")
            rfr_msg: discord.Message = await channel.send(embed=embed)
            self.rfr_database_manager.add_rfr_message(ctx.guild.id, channel.id, rfr_msg.id)
            await self.overwrite_channel_add_reaction_perms(ctx.guild, channel)
            await ctx.send(
                f"Your react for role message ID is {rfr_msg.id}, it's in {channel.mention}. You can use the other "
                "k!rfr subcommands to change the message and add functionality as required.")
            await del_msg.delete()

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command(name="delete", aliases=["deleteMsg", "deleteMessage"])
    async def rfr_delete_message(self, ctx: commands.Context):
        """
        Deletes an existing rfr message. User is prompted for (in this order) channel ID/name/mention, message ID/URL,
        Y/N confirmation. User needs admin perms to use.
        :param ctx: Context of the command
        :return:
        """
        await ctx.send(
            "Okay, this will delete an existing react for role message. I'll need some details first though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        await ctx.send("Please confirm that you would indeed like to delete the react for role message.")
        if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
            await ctx.send("Ok")
            rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg.id)
            self.rfr_database_manager.remove_rfr_message_emoji_roles(rfr_msg_row[3])
            self.rfr_database_manager.remove_rfr_message(ctx.guild.id, channel.id, msg.id)
            await msg.delete()
            await ctx.send("ReactForRole Message deleted")
        else:
            await ctx.send("Cancelled command.")

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
        embed = self.get_embed_from_message(msg)
        await ctx.send(f"Your current description is {embed.description}. Please enter your new description.")
        desc = await self.prompt_for_input(ctx, "description")
        if desc != "":
            await ctx.send(f"Your new description would be {desc}. Please confirm that you'd like this change.")
            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                embed.description = desc
                await msg.edit(embed=embed)
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
        embed = self.get_embed_from_message(msg)
        await ctx.send(f"Your current title is {embed.title}. Please enter your new title.")
        title = await self.prompt_for_input(ctx, "title")
        if title != "":
            await ctx.send(f"Your new title would be {title}. Please confirm that you'd like this change.")
            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                embed.title = title
                await msg.edit(embed=embed)
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
        embed = self.get_embed_from_message(msg)
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
                embed.set_thumbnail(url=str(image.url))
                await msg.edit(embed=embed)
                await ctx.send("Okay, set the thumbnail of the thumbnail to your desired image. This will error if you "
                               "delete the message you sent with the image, so make sure you don't.")
        elif isinstance(image, str):
            # no attachment in message, just a raw URL in content
            img_url = await self.get_image_from_url(ctx, image)
            embed.set_thumbnail(url=img_url)
            await msg.edit(embed=embed)
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
                    # fetch rfr messages
                    guild: discord.Guild = ctx.guild
                    text_channels: List[discord.TextChannel] = guild.text_channels
                    guild_rfr_messages = self.rfr_database_manager.get_guild_rfr_messages(guild.id)
                    for rfr_message in guild_rfr_messages:
                        channel: discord.TextChannel = discord.utils.get(text_channels, id=rfr_message[1])
                        msg: discord.Message = await channel.fetch_message(id=rfr_message[2])
                        embed: discord.Embed = self.get_embed_from_message(msg)
                        length = self.get_number_of_embed_fields(embed)
                        for i in range(length):
                            field = embed.fields[i]
                            embed.set_field_at(i, name=field.name, value=field.value, inline=change_all == "Y")
                        await msg.edit(embed=embed)
                    await ctx.send("Okay, the process should be finished now. Please check.")
            elif input_comm.lstrip().rstrip().lower() == "specific":
                # try and get specific message
                await ctx.send("Okay, I'll need the information about the specific rfr message.")
                msg, channel = await self.get_rfr_message_from_prompts(ctx)
                embed: discord.Embed = self.get_embed_from_message(msg)
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
                        length = self.get_number_of_embed_fields(embed)
                        for i in range(length):
                            field = embed.fields[i]
                            embed.set_field_at(i, name=field.name, value=field.value, inline=yes_no == "Y")
                        await msg.edit(embed=embed)
                        await ctx.send("Okay, should be done. Please check.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @edit_group.command(name="fixEmbed")
    async def rfr_fix_embed(self, ctx: commands.Context):
        """
        Cosmetic fix method if the bot ever has a moment and doesn't react with the correct emojis/has duplicates.
        """
        msg, chnl = await self.get_rfr_message_from_prompts(ctx)
        await self.overwrite_channel_add_reaction_perms(chnl.guild, chnl)
        emb = self.get_embed_from_message(msg)
        reacts: List[Union[discord.PartialEmoji, discord.Emoji, str]] = [x.emoji for x in msg.reactions]
        if not emb:
            logger.error(
                f"RFR: Can't find embed for message id {msg.id}, channel {chnl.id}, guild id {ctx.guild.id}.")
        else:
            er_id, _, _, _ = self.rfr_database_manager.get_rfr_message(ctx.guild.id, chnl.id, msg.id)
            if not er_id:
                logger.error(
                    f"RFR: Can't find rfr message with {msg.id}, channel {chnl.id}, guild id {ctx.guild.id}. DB ER_ID : {er_id}")
            else:
                rfr_er = self.rfr_database_manager.get_rfr_message_emoji_roles(er_id)
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
        rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg.id)

        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        await ctx.send("Okay, found the message you want to add to.")
        remaining_slots = 20 - self.get_number_of_embed_fields(self.get_embed_from_message(msg))

        if remaining_slots == 0:
            await ctx.send(
                "Unfortunately due to discord limitations that message cannot have any more reactions. If you want I "
                "can create another message in the same channel though. Shall I do that?")

            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await ctx.send(
                    "Okay, I'll continue then. The new message will have the same title and description as the "
                    "old one.")
                old_embed = self.get_embed_from_message(msg)
                embed: discord.Embed = discord.Embed(title=old_embed.title, description=old_embed.description)
                embed.set_thumbnail(
                    url=koalabot.KOALA_IMAGE_URL)
                msg: discord.Message = await channel.send(embed=embed)
                msg_id = msg.id
                channel = msg.channel
                self.rfr_database_manager.add_rfr_message(ctx.guild.id, channel.id, msg_id)
                await ctx.send(f"Okay, the new message has ID {msg.id} and is in {msg.channel.mention}.")
                rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg_id)
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
        rfr_embed = self.get_embed_from_message(msg)

        for emoji_role in emoji_role_list:
            discord_emoji = emoji_role[0]
            role = emoji_role[1]

            if discord_emoji in [x.name for x in rfr_embed.fields]:
                await ctx.send("Found duplicate emoji in the message, I'm not accepting it.")
            elif role in [x.value for x in rfr_embed.fields]:
                await ctx.send("Found duplicate role in the message, I'm not accepting it.")
            else:
                if isinstance(discord_emoji, str):
                    self.rfr_database_manager.add_rfr_message_emoji_role(rfr_msg_row[3], emoji.demojize(discord_emoji),
                                                                         role.id)
                else:
                    self.rfr_database_manager.add_rfr_message_emoji_role(rfr_msg_row[3], str(discord_emoji), role.id)
                rfr_embed.add_field(name=str(discord_emoji), value=role.mention, inline=False)
                await msg.add_reaction(discord_emoji)

                if isinstance(discord_emoji, str):
                    logger.info(
                        f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                        f"({str(channel.id)}, {str(ctx.guild.id)}) with emoji {discord_emoji}.")
                else:
                    logger.info(
                        f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                        f"({str(channel.id)}, {str(ctx.guild.id)}) with emoji {discord_emoji.id}.")

        await msg.edit(embed=rfr_embed)
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
        rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg.id)

        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        await ctx.send("Okay, found the message you want to remove roles from.")
        remaining_slots = self.get_number_of_embed_fields(self.get_embed_from_message(msg))

        if remaining_slots == 0:
            await ctx.send(
                "Okay, it looks like you've already gotten rid of all roles from this message. Would you like me to del"
                "ete the message too?")

            if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                await ctx.send("Okay, deleting that message and removing it from the database.")
                self.rfr_database_manager.remove_rfr_message(ctx.guild.id, channel.id, msg.id)
                await msg.delete()
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
            rfr_embed: discord.Embed = self.get_embed_from_message(msg)
            rfr_embed_fields = rfr_embed.fields
            new_embed = discord.Embed(title=rfr_embed.title, description=rfr_embed.description,
                                      colour=KOALA_GREEN)
            new_embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png")
            new_embed.set_footer(text="ReactForRole")
            removed_field_indexes = []
            reactions_to_remove: List[discord.Reaction] = []

            for row in wanted_removals:
                if isinstance(row, discord.Emoji) or isinstance(row, str):
                    field_index = [x.name for x in rfr_embed_fields].index(str(row))
                    if isinstance(row, str):
                        self.rfr_database_manager.remove_rfr_message_emoji_role(rfr_msg_row[3],
                                                                                emoji_raw=emoji.demojize(row))
                    else:
                        self.rfr_database_manager.remove_rfr_message_emoji_role(rfr_msg_row[3], emoji_raw=row)
                else:
                    # row is instance of role
                    field_index = [x.value for x in rfr_embed_fields].index(row.mention)
                    self.rfr_database_manager.remove_rfr_message_emoji_role(rfr_msg_row[3], role_id=row.id)

                field = rfr_embed_fields[field_index]
                removed_field_indexes.append(field_index)
                reaction_emoji = await self.get_first_emoji_from_str(ctx, field.name)
                reaction: discord.Reaction = [x for x in msg.reactions if str(x.emoji) == str(reaction_emoji)][0]
                reactions_to_remove.append(reaction)

            new_embed_fields = [field for field in rfr_embed_fields if
                                rfr_embed_fields.index(field) not in removed_field_indexes]

            for field in new_embed_fields:
                new_embed.add_field(name=field.name, value=field.value, inline=False)

            if self.get_number_of_embed_fields(new_embed) == 0:
                await ctx.send("I see you've removed all emoji-role combinations from this react for role message. "
                               "Would you like to delete this message?")

                if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
                    await ctx.send("Okay, I'll delete the message then.")
                    self.rfr_database_manager.remove_rfr_message(ctx.guild.id, channel.id, msg.id)
                    await msg.delete()
                    return

            for reaction in reactions_to_remove:
                await reaction.clear()
            await msg.edit(embed=new_embed)
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
        if payload.guild_id is not None and not payload.member.bot:
            rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
                                                                    payload.message_id)
            if not rfr_message:
                return

            try:
                member_role = await self.get_role_member_info(payload.emoji, payload.guild_id,
                                                              payload.channel_id,
                                                              payload.message_id, payload.user_id)
            except ReactionException as e:
                logger.error("RFR Member role not found", exc_info=e)
                # Remove the reaction
                guild: discord.Guild = self.bot.get_guild(payload.guild_id)
                channel: discord.TextChannel = guild.get_channel(payload.channel_id)
                msg: discord.Message = await channel.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, payload.member)
            else:
                if self.can_have_rfr_role(member_role[0]):
                    await member_role[0].add_roles(member_role[1])
                else:
                    # Remove all rfr roles from member
                    role_ids = self.rfr_database_manager.get_guild_rfr_roles(payload.guild_id)
                    roles: List[discord.Role] = []
                    for role_id in role_ids:
                        role = discord.utils.get(member_role[0].guild.roles, id=role_id)
                        if not role:
                            continue
                        roles.append(role)
                    for role_to_remove in roles:
                        await member_role[0].remove_roles(role_to_remove)
                    # Remove members' reaction from all rfr messages in guild
                    guild_rfr_messages = self.rfr_database_manager.get_guild_rfr_messages(payload.guild_id)
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
    async def rfr_add_guild_required_role(self, ctx: commands.Context, role_str: str):
        """
        Adds a role to perms to use rfr functionality in a server, so you can specify that you need, e.g. "@Student" to
        be able to use rfr functionality in the server. It's server-wide permissions handling however. By default anyone
        can use rfr functionality in the server. User needs to have admin perms to use.
        :param ctx: Context of the command
        :param role_str: Role ID/name/mention
        :return:
        """
        try:
            role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
            await ctx.send(f"Okay, I'll add {role.name} to the list of roles required for RFR usage on the server.")
            self.rfr_database_manager.add_guild_rfr_required_role(ctx.guild.id, role.id)
        except (commands.CommandError, commands.BadArgument):
            await ctx.send("Found an issue with your provided argument, couldn't get an actual role. Please try again.")

    @commands.check(koalabot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command("removeRequiredRole")
    async def rfr_remove_guild_required_role(self, ctx: commands.Context, role_str: str):
        """
        Removes a role from perms for use of rfr functionality in a server, so you can specify that you need, e.g.
        "@Student" to be able to use rfr functionality in the server. It's server-wide permissions handling however. By
        default anyone can use rfr functionality in the server. User needs to have admin perms to use.
        :param ctx: Context of the command
        :param role_str: Role ID/name/mention
        :return:
        """
        try:
            role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
            await ctx.send(
                f"Okay, I'll remove {role.name} from the list of roles required for RFR usage on the server.")
            self.rfr_database_manager.remove_guild_rfr_required_role(ctx.guild.id, role.id)
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
        role_ids = self.rfr_database_manager.get_guild_rfr_required_roles(ctx.guild.id)
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
            rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
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
        required_roles: List[int] = self.rfr_database_manager.get_guild_rfr_required_roles(member.guild.id)
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
        rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg_id)
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
            raise ReactionException(ReactionErrorCode.UNKNOWN_MEMBER_REACTION, user_id, guild_id)
        channel: discord.TextChannel = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            raise ReactionException(ReactionErrorCode.UNKNOWN_CHANNEL_REACTION, channel_id, guild_id)
        message: discord.Message = await channel.fetch_message(message_id)
        if not message:
            raise ReactionException(ReactionErrorCode.UNKNOWN_MESSAGE_REACTION, message_id, guild_id)
        embed: discord.Embed = self.get_embed_from_message(message)

        if emoji_reacted.is_unicode_emoji():  # Unicode Emoji
            rep = emoji.emojize(emoji_reacted.name)
            if not rep:
                rep = emoji.emojize(emoji_reacted.name, use_aliases=True)

            field = await self.get_field_by_emoji(embed, rep)
            if not field:
                raise ReactionException(ReactionErrorCode.UNKNOWN_REACTION_FIELD, message_id, guild_id)
            role_str: str = field
            if not role_str:
                raise ReactionException(ReactionErrorCode.UNKNOWN_REACTION_ROLE, field, guild_id)
            role: discord.Role = discord.utils.get(guild.roles, mention=role_str.lstrip().rstrip())
            if not role:
                raise ReactionException(ReactionErrorCode.UNKNOWN_REACTION_ROLE, role, guild_id)
        else:  # Custom Emoji
            rep = str(emoji_reacted)
            field = await self.get_field_by_emoji(embed, rep)
            if not field:
                raise ReactionException(ReactionErrorCode.UNKNOWN_REACTION_FIELD, message_id, guild_id)
            role_str = field
            role: discord.Role = discord.utils.get(guild.roles, mention=role_str.lstrip().rstrip())
        return member, role

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
            if len(emoji_role) > 2:
                raise commands.BadArgument("Too many categories/etc on one line.")
            emoji: Union[discord.Emoji, str] = await self.get_first_emoji_from_str(ctx, emoji_role[0].strip())
            if not emoji:
                await ctx.send(f"Yeah, didn't find emoji for `{emoji_role[0]}`")
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
            raw_emoji = await self.get_first_emoji_from_str(ctx, row.strip())
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

    async def overwrite_channel_add_reaction_perms(self, guild: discord.Guild, channel: discord.TextChannel):
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
        await channel.set_permissions(role, overwrite=overwrite)
        bot_members = [member for member in guild.members if member.bot and member.id == self.bot.user.id]
        overwrite.update(add_reactions=True)
        for bot_member in bot_members:
            await channel.set_permissions(bot_member, overwrite=overwrite)

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

    def get_embed_from_message(self, msg: discord.Message) -> Optional[discord.Embed]:
        """
        Gets the embed from a given message. Yup. That's it.
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

    def get_number_of_embed_fields(self, embed: discord.Embed) -> int:
        """
        Gets the number of fields in an embed.
        :param embed: Embed to check
        :return: Number of embed fields.
        """
        return len(embed.fields)

    async def get_first_emoji_from_str(self, ctx: commands.Context, content: str) -> Optional[
        Union[discord.Emoji, str]]:
        """
        Gets the first emoji in a string input, custom or not. Doesn't work with custom emojis the bot doesn't have
        access to.
        :param ctx: Context of the original command
        :param content: Message content
        :return: Emoji if there is a valid one. Otherwise None.
        """
        # First check for a custom discord emoji in the string
        search_result = CUSTOM_EMOJI_REGEXP.search(content)
        if not search_result:
            # Check for a unicode emoji in the string
            search_result = UNICODE_EMOJI_REGEXP.search(content)
            if not search_result:
                return None
            return content
        else:
            emoji_str = search_result.group().strip()
            try:
                discord_emoji: discord.Emoji = await commands.EmojiConverter().convert(ctx, emoji_str)
                return discord_emoji
            except commands.CommandError:
                await ctx.send(
                    "An error occurred when trying to get the emoji. Please contact the bot developers for support.")
                return None
            except commands.BadArgument:
                await ctx.send("Couldn't get the emoji you used - is it from this server or a server I'm in?")
                return None

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


def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(ReactForRole(bot))
