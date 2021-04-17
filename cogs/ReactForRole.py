#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

Author: Anan Venkatesh
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import re
from typing import *

import discord
import emoji
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager, KoalaColours
from utils.KoalaUtils import wait_for_message

# Libs

# Constants

UNICODE_DISCORD_EMOJI_REGEXP: re.Pattern = re.compile("^:(\w+):$")
CUSTOM_EMOJI_REGEXP: re.Pattern = re.compile("^<a?:(\w+):(\d+)>$")
UNICODE_EMOJI_REGEXP: re.Pattern = re.compile(emoji.get_emoji_regexp())


def rfr_is_enabled(ctx):
    """
    A command used to check if the guild has enabled rfr
    e.g. @commands.check(rfr_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "ReactForRole")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class ReactForRole(commands.Cog):
    """
    A discord.py cog pertaining to a React for Role system to allow for automation in getting roles.
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("ReactForRole", 0, True, True)
        self.rfr_database_manager = ReactForRoleDBManager(KoalaBot.database_manager)
        self.rfr_database_manager.create_tables()

    @commands.group(name="rfr", aliases=["reactForRole", "react_for_role"])
    async def react_for_role_group(self, ctx: commands.Context):
        """
        Group of commands for React for Role (rfr) functionality.
        :param ctx: Context of the command
        :return:
        """
        return

    @commands.check(KoalaBot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command(name="createMsg", aliases=["create", "createMessage"])
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
                "Okay, what would you like the title of the react for role message to be? Please enter within 30"
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
                f"Okay, the title of the message will be \"{title}\". What do you want the description to be?")
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
            embed: discord.Embed = discord.Embed(title=title, description=desc, colour=KoalaColours.KOALA_GREEN)
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

    @commands.check(KoalaBot.is_admin)
    @commands.check(rfr_is_enabled)
    @react_for_role_group.command(name="deleteMsg", aliases=["delete", "deleteMessage"])
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

    @commands.check(KoalaBot.is_admin)
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

    @commands.check(KoalaBot.is_admin)
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

    @commands.check(KoalaBot.is_admin)
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
                    url=KoalaBot.KOALA_IMAGE_URL)
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
                    KoalaBot.logger.info(
                        f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                        f"({str(channel.id)}, {str(ctx.guild.id)}) with emoji {discord_emoji}.")
                else:
                    KoalaBot.logger.info(
                        f"ReactForRole: Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} "
                        f"({str(channel.id)}, {str(ctx.guild.id)}) with emoji {discord_emoji.id}.")

        await msg.edit(embed=rfr_embed)
        await ctx.send("Okay, you should see the message with its new emojis now.")

    @commands.check(KoalaBot.is_admin)
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
                                      colour=KoalaColours.KOALA_GREEN)
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
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Event listener for adding a reaction. Doesn't need message to be in loaded cache.
        Gives the user a role if they can get it, if not strips all their roles and removes their reacts.
        :param payload: RawReactionActionEvent that happened
        :return:
        """
        if not payload.member.bot:
            rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
                                                                    payload.message_id)
            if not rfr_message:
                return
            member_role = self.get_role_member_info(payload.emoji, rfr_message[3], payload.guild_id, payload.channel_id,
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
                        KoalaBot.logger.error(
                            f"ReactForRole: Guild RFR messages is empty on raw reaction add. Please check"
                            f" guild ID {payload.guild_id}")

                    else:
                        for guild_rfr_message in guild_rfr_messages:
                            guild: discord.Guild = member_role[0].guild
                            channel: discord.TextChannel = guild.get_channel(guild_rfr_message[1])
                            msg: discord.Message = await channel.fetch_message(guild_rfr_message[2])
                            for x in msg.reactions:
                                await x.remove(payload.member)

    @commands.check(KoalaBot.is_admin)
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

    @commands.check(KoalaBot.is_admin)
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

    @commands.check(KoalaBot.is_admin)
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
                KoalaBot.logger.error(f"ReactForRole: Couldn't find role {role_id} in guild {ctx.guild.id}. Please "
                                      f"check.")
            else:
                msg_str += f"{role.mention}\n"
        await ctx.send(msg_str)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Event listener for removing a reaction. Doesn't need message to be in loaded cache. Removes the role from the
        user if they have it, else does nothing.
        :param payload: RawReactionActionEvent that happened.
        :return:
        """

        rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
                                                                payload.message_id)
        if not rfr_message:
            return
        member_role = self.get_role_member_info(payload.emoji, rfr_message[3], payload.guild_id, payload.channel_id,
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

    def get_role_member_info(self, emoji_reacted: discord.PartialEmoji, emoji_role_id: int, guild_id: int,
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
        if emoji_reacted.is_unicode_emoji():
            rep = emoji.demojize(emoji_reacted.name)
            role_id = self.rfr_database_manager.get_rfr_reaction_role_by_emoji_str(emoji_role_id, rep)
        elif emoji_reacted.is_custom_emoji():
            rep = str(emoji_reacted)
            role_id = self.rfr_database_manager.get_rfr_reaction_role_by_emoji_str(emoji_role_id, rep)
        else:
            KoalaBot.logger.error(
                f"ReactForRole: Database error, guild {guild_id} has no entry in rfr database for message_id "
                f"{message_id} in channel_id {channel_id}. Please check this.")
            return
        guild: discord.Guild = self.bot.get_guild(guild_id)
        member: discord.Member = discord.utils.get(guild.members, id=user_id)
        if not member:
            return
        if not role_id:
            return
        role: discord.Role = discord.utils.get(guild.roles, id=role_id)
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

    async def prompt_for_input(self, ctx: commands.Context, input_type: str) -> str:
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


class ReactForRoleDBManager:
    """
    A class for interacting with the KoalaBot ReactForRole database
    """

    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager: KoalaDBManager.KoalaDBManager = database_manager

    def get_parent_database_manager(self):
        """
        Gets the parent database manager, i.e. the KoalaDBManager class this takes from
        :return: parent database manager
        """
        return self.database_manager

    def create_tables(self):
        """
        Creates all the tables associated with the React For Role extension
        """
        sql_create_guild_rfr_message_ids_table = """
        CREATE TABLE IF NOT EXISTS GuildRFRMessages (
        guild_id integer NOT NULL,
        channel_id integer NOT NULL,
        message_id integer NOT NULL,
        emoji_role_id integer,
        PRIMARY KEY (emoji_role_id),
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id),
        UNIQUE (guild_id, channel_id, message_id)
        );
        """
        sql_create_rfr_message_emoji_roles_table = """
        CREATE TABLE IF NOT EXISTS RFRMessageEmojiRoles (
        emoji_role_id integer NOT NULL,
        emoji_raw text NOT NULL,
        role_id integer NOT NULL,
        PRIMARY KEY (emoji_role_id, emoji_raw, role_id),
        FOREIGN KEY (emoji_role_id) REFERENCES GuildRFRMessages(emoji_role_id),
        UNIQUE (emoji_role_id, emoji_raw),
        UNIQUE  (emoji_role_id, role_id)
        );
        """
        sql_create_rfr_required_roles_table = """
        CREATE TABLE IF NOT EXISTS GuildRFRRequiredRoles (
        guild_id integer NOT NULL,
        role_id integer NOT NULL,
        PRIMARY KEY (guild_id, role_id),
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id),
        UNIQUE (guild_id, role_id)
        );
        """
        self.database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)
        self.database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)
        self.database_manager.db_execute_commit(sql_create_rfr_required_roles_table)

    def add_rfr_message(self, guild_id: int, channel_id: int, message_id: int):
        """
        Add an rfr message to a guild. Table stores a unique emoji_role_id to prevent the same combination
        appearing twice on a given message
        :param guild_id: ID of the guild
        :param channel_id: ID of the channel the rfr message is in
        :param message_id: ID of the rfr message
        :return:
        """
        self.database_manager.db_execute_commit(
            f"""INSERT INTO GuildRFRMessages  (guild_id, channel_id, message_id) VALUES ({guild_id}, {channel_id}, {message_id});""")

    def add_rfr_message_emoji_role(self, emoji_role_id: int, emoji_raw: str, role_id: int):
        """
        Add an emoji-role combination to an rfr message.
        :param emoji_role_id: unique ID/key
        :param emoji_raw: raw emoji representation in string format
        :param role_id: ID of the role to give on react
        :return:
        """
        self.database_manager.db_execute_commit(
            f"""INSERT INTO RFRMessageEmojiRoles (emoji_role_id, emoji_raw, role_id) VALUES ({emoji_role_id}, \"{emoji_raw}\", {role_id});""")

    def remove_rfr_message_emoji_role(self, emoji_role_id: int, emoji_raw: str = None, role_id: int = None):
        """
        Remove an emoji-role combination from the rfr message database. Uses the unique emoji_role_id to identify the
        specific combo. Only removes one emoji-role combo
        :param emoji_role_id: unique ID/key
        :param emoji_raw: raw string representation of the emoji
        :param role_id: ID of the role to give on react
        :return:
        """
        if not emoji_raw:
            self.database_manager.db_execute_commit(
                f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND role_id = {role_id};""")
        else:
            self.database_manager.db_execute_commit(
                f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\";""")

    def remove_rfr_message_emoji_roles(self, emoji_role_id: int):
        """
        Removes all emoji-role combos with the same emoji_role_id i.e. on the same message.
        :param emoji_role_id: unique ID/key
        :return:
        """
        self.database_manager.db_execute_commit(
            f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id};""")

    def remove_rfr_message(self, guild_id: int, channel_id: int, message_id: int):
        """
        Removes an rfr message from the rfr message database, and also removes all emoji-role combos as part of it.
        :param guild_id: Guild ID of the rfr message
        :param channel_id: Channel ID of the rfr message
        :param message_id: Message ID of the rfr message
        :return:
        """
        emoji_role_id = self.get_rfr_message(guild_id, channel_id, message_id)
        if not emoji_role_id:
            return
        else:
            self.remove_rfr_message_emoji_roles(emoji_role_id[3])
        self.database_manager.db_execute_commit(
            f"""DELETE FROM GuildRFRMessages WHERE guild_id = {guild_id} AND channel_id = {channel_id} AND message_id = {message_id};""")

    def get_rfr_message(self, guild_id: int, channel_id: int, message_id: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Gets the unique rfr message that is specified by the guild ID, channel ID and message ID.
        :param guild_id: Guild ID of the rfr message
        :param channel_id: Channel ID of the rfr message
        :param message_id: Message ID of the rfr message
        :return: RFR message info of the specific message if found, otherwise None.
        """
        rows: List[Tuple[int, int, int, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM GuildRFRMessages WHERE guild_id = {guild_id} AND channel_id = {channel_id} AND message_id = {message_id};""")
        if not rows:
            return
        return rows[0]

    def get_guild_rfr_messages(self, guild_id: int):
        """
        Gets all rfr messages in a given guild, from the guild ID
        :param guild_id: ID of the guild
        :return: List of rfr messages in the guild.
        """
        rows: List[Tuple[int, int, int, int]] = self.database_manager.db_execute_select(
            "SELECT * FROM GuildRFRMessages WHERE guild_id = ?;", args=[guild_id])
        return rows

    def get_guild_rfr_roles(self, guild_id: int) -> List[int]:
        """
        Returns all role IDs of roles given by RFR messages in a guild

        :param guild_id: Guild ID to check in.
        :return: Role IDs of RFR roles in a specific guild
        """
        rfr_messages: List[Tuple[int, int, int, int]] = self.database_manager.db_execute_select(
            "SELECT * FROM GuildRFRMessages WHERE guild_id = ?;", guild_id)
        if not rfr_messages:
            return []
        role_ids: List[int] = []
        for rfr_message in rfr_messages:
            emoji_role_id = rfr_message[3]
            roles: List[Tuple[int, str, int]] = self.get_rfr_message_emoji_roles(emoji_role_id)
            if not roles:
                continue
            ids: List[int] = [x[2] for x in roles]
            role_ids.extend(ids)
        return role_ids

    def get_rfr_message_emoji_roles(self, emoji_role_id: int):
        """
        Returns all the emoji-role combinations on an rfr message

        :param emoji_role_id: emoji-role combo identifier
        :return: List of rows in the database if found, otherwise None
        """
        rows: List[Tuple[int, str, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id};""")
        if not rows:
            return
        return rows

    def get_rfr_reaction_role(self, emoji_role_id: int, emoji_raw: str, role_id: int):
        """
        Returns a specific emoji-role combo on an rfr message

        :param emoji_role_id: emoji-role combo identifier
        :param emoji_raw: raw string representation of the emoji
        :param role_id: role ID of the emoji-role combo
        :return: Unique row corresponding to a specific emoji-role combo
        """
        rows: List[Tuple[int, str, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\" AND role_id = {role_id};""")
        if not rows:
            return
        return rows[0]

    def get_rfr_reaction_role_by_emoji_str(self, emoji_role_id: int, emoji_raw: str) -> Optional[int]:
        """
        Gets a role ID from the emoji_role_id and the emoji associated with that role in the emoji-role combo
        :param emoji_role_id: emoji-role combo identifier
        :param emoji_raw: raw string representation of the emoji
        :return: role ID of the emoji-role combo
        """
        rows: Tuple[int, str, int] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\";""")
        if not rows:
            return
        return rows[0][2]

    def add_guild_rfr_required_role(self, guild_id: int, role_id: int):
        """
        Adds a role to the list of roles required to use rfr functionality in a guild.
        :param guild_id: guild ID
        :param role_id: role ID
        :return:
        """
        self.database_manager.db_execute_commit("INSERT INTO GuildRFRRequiredRoles VALUES (?,?);",
                                                args=[guild_id, role_id])

    def remove_guild_rfr_required_role(self, guild_id: int, role_id: int):
        """
        Removes a role from the list of roles required to use rfr functionality in a guild
        :param guild_id: guild ID
        :param role_id: role ID
        :return:
        """
        self.database_manager.db_execute_commit("DELETE FROM GuildRFRRequiredRoles WHERE guild_id = ? AND role_id = ?",
                                                args=[guild_id, role_id])

    def get_guild_rfr_required_roles(self, guild_id) -> List[int]:
        """
        Gets the list of role IDs of roles required to use rfr functionality in a guild
        :param guild_id: guild ID
        :return: List of role IDs
        """
        rows = self.database_manager.db_execute_select("SELECT * FROM GuildRFRRequiredRoles WHERE guild_id = ?",
                                                       args=[guild_id])
        role_ids = [x[1] for x in rows]
        if not role_ids:
            return []
        return role_ids


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(ReactForRole(bot))
