#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

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

# Libs

# Constants
UNICODE_DISCORD_EMOJI_REGEXP: re.Pattern = re.compile("^:(\w+):$")
CUSTOM_EMOJI_REGEXP: re.Pattern = re.compile("^<a?:(\w+):(\d+)>$")
UNICODE_EMOJI_REGEXP: re.Pattern = re.compile(emoji.get_emoji_regexp())


class ReactForRole(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        KoalaBot.database_manager.create_base_tables()
        KoalaBot.database_manager.insert_extension("ReactForRole", 0, True, True)
        self.rfr_database_manager = ReactForRoleDBManager(KoalaBot.database_manager)
        self.rfr_database_manager.create_tables()

    @commands.group(name="reactForRole", aliases=["rfr", "react_for_role", "ReactForRole"])
    async def react_for_role_group(self, ctx: commands.Context):
        return

    @react_for_role_group.command(name="createMessage")
    async def rfr_create_message(self, ctx: commands.Context):
        await ctx.send(
            "Okay, this will create a new react for role message in a channel of your choice."
            "\nNote: The channel you specify will have its permissions edited to make it such that members are unable "
            "to add new reactions to messages, they can only reaction with existing ones. Please keep this in mind, or"
            " setup another channel entirely for this.")
        channel_raw = await self.prompt_for_input(ctx, "channel ID, name or mention")
        channel: discord.TextChannel = await commands.TextChannelConverter().convert(ctx, channel_raw)
        if not channel:
            await ctx.send("Sorry, you didn't specify a valid channel ID, mention or name. Please restart the command.")
        else:
            del_msg = await channel.send(f"This should be a thing sent in the right channel.")
            await ctx.send(
                "Okay, what would you like the title of the react for role message to be? Please enter within 30"
                " seconds.")
            x = await self.wait_for_message(self.bot, ctx)
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
            y = await self.wait_for_message(self.bot, ctx)
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
            await ctx.send(f"Okay, the description of the message will be \"{desc}\".")
            embed: discord.Embed = discord.Embed(title=title, description=desc, colour=KoalaColours.KOALA_GREEN)
            embed.set_footer(text="ReactForRole")
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png")
            await ctx.send(f"Okay, I'll create the react for role message now.")
            rfr_msg: discord.Message = await channel.send(embed=embed)
            self.rfr_database_manager.add_rfr_message(ctx.guild.id, channel.id, rfr_msg.id)
            await self.overwrite_channel_add_reaction_perms(ctx.guild, channel)
            await ctx.send(
                f"Your react for role message ID is {rfr_msg.id}, it's in {channel.mention}. You can use the other "
                "k!rfr subcommands to change the message and add functionality as required.")
            await del_msg.delete()

    @react_for_role_group.command(name="deleteMessage")
    async def rfr_delete_message(self, ctx: commands.Context):
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

    @edit_group.command(name="description", aliases=["desc"])
    async def rfr_edit_description(self, ctx: commands.Context):
        await ctx.send("Okay, this will edit the description of an existing react for role message. I'll need some "
                       "details first though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        embed = self.get_embed_from_message(msg)
        await ctx.send(f"Your current description is {embed.description}. Please enter your new description.")
        desc = await self.prompt_for_input(ctx, "description")
        await ctx.send(f"Your new description would be {desc}. Please confirm that you'd like this change.")
        if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
            embed.description = desc
            await msg.edit(embed=embed)
        else:
            await ctx.send("Okay, cancelling command.")

    @edit_group.command(name="title")
    async def rfr_edit_title(self, ctx: commands.Context):
        await ctx.send("Okay, this will edit the title of an existing react for role message. I'll need some details "
                       "first though.")
        msg, channel = await self.get_rfr_message_from_prompts(ctx)
        embed = self.get_embed_from_message(msg)
        await ctx.send(f"Your current title is {embed.title}. Please enter your new title.")
        title = await self.prompt_for_input(ctx, "title")
        await ctx.send(f"Your new title would be {title}. Please confirm that you'd like this change.")
        if (await self.prompt_for_input(ctx, "Y/N")).lstrip().strip().upper() == "Y":
            embed.title = title
            await msg.edit(embed=embed)
        else:
            await ctx.send("Okay, cancelling command.")

    @edit_group.command(name="addRoles")
    async def rfr_add_roles_to_msg(self, ctx: commands.Context):
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
                    url="https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png")
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
            "Okay. Can I get the roles and emojis you want added to the message in a list with format: \n\"<emoji>,"
            " <role>\"\n\"<emoji>, <role>\"\n\"<emoji>, <role>\"\netc. You can get a new line by using SHIFT + ENTER.")
        await ctx.send(
            f"Please note however that you've only got {remaining_slots} emoji-role combinations you can enter. I'll "
            "therefore only take the first {remaining_slots} you do.")
        input_role_emojis = (await self.wait_for_message(self.bot, ctx))[0].content
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
                        f"Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} ({str(channel.id)}, "
                        f"{str(ctx.guild.id)}) with emoji {discord_emoji}.")
                else:
                    KoalaBot.logger.info(
                        f"Added role ID {str(role.id)} to rfr message (channel, guild) {msg.id} ({str(channel.id)}, "
                        f"{str(ctx.guild.id)}) with emoji {discord_emoji.id}.")
        await msg.edit(embed=rfr_embed)
        await ctx.send("Okay, you should see the message with its new emojis now.")

    @edit_group.command(name="removeRoles")
    async def rfr_remove_roles_from_msg(self, ctx: commands.Context):
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
            input_emoji_roles = (await self.wait_for_message(self.bot, ctx, 120))[0].content
            wanted_removals = await self.parse_emoji_or_roles_input_str(ctx, input_emoji_roles)
            rfr_embed: discord.Embed = self.get_embed_from_message(msg)
            rfr_embed_fields = rfr_embed.fields
            new_embed = discord.Embed(title=rfr_embed.title, description=rfr_embed.description)
            new_embed.set_footer(text="ReactForRole")
            removed_field_indexes = []
            reactions_to_remove: List[discord.Reaction] = []
            KoalaBot.logger.info(f"{[str(x) for x in msg.reactions]}")
            KoalaBot.logger.info(f"{msg.reactions}")
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
                KoalaBot.logger.info(f"reaction_emoji line 223 = {str(reaction_emoji)}")
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
        rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
                                                                payload.message_id)
        if not rfr_message:
            return
        member_role = self.get_role_member_info(payload.emoji, rfr_message[3], payload.guild_id, payload.channel_id,
                                                payload.message_id, payload.user_id)
        if await self.can_have_rfr_role(member_role[0]):
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
                KoalaBot.logger.error("Guild RFR messages is empty on raw reaction add. Please check")
                print(self.rfr_database_manager.get_guild_rfr_messages(payload.guild_id))
            else:
                for guild_rfr_message in guild_rfr_messages:
                    guild: discord.Guild = member_role[0].guild
                    channel: discord.TextChannel = guild.get_channel(guild_rfr_message[1])
                    msg: discord.Message = await channel.fetch_message(guild_rfr_message[2])
                    for x in msg.reactions:
                        await x.remove(payload.member)

    @react_for_role_group.command("addRequiredRole")
    async def rfr_add_guild_required_role(self, ctx: commands.Context, role_str: str):
        try:
            role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
            await ctx.send(f"Okay, I'll add {role.name} to the list of roles required for RFR usage on the server.")
            self.rfr_database_manager.add_guild_rfr_required_role(ctx.guild.id, role.id)
        except (commands.CommandError, commands.BadArgument):
            await ctx.send("Found an issue with your provided argument, couldn't get an actual role. Please try again.")

    @react_for_role_group.command("removeRequiredRole")
    async def rfr_remove_guild_required_role(self, ctx: commands.Context, role_str: str):
        try:
            role: discord.Role = await commands.RoleConverter().convert(ctx, role_str)
            await ctx.send(
                f"Okay, I'll remove {role.name} from the list of roles required for RFR usage on the server.")
            self.rfr_database_manager.remove_guild_rfr_required_role(ctx.guild.id, role.id)
        except (commands.CommandError, commands.BadArgument):
            await ctx.send("Found an issue with your provided argument, couldn't get an actual role. Please try again.")

    @react_for_role_group.command("listRequiredRoles")
    async def rfr_list_guild_required_roles(self, ctx: commands.Context):
        role_ids = self.rfr_database_manager.get_guild_rfr_required_roles(ctx.guild.id)
        msg_str = "You will need one of these roles to react to rfr messages on this server:\n"
        KoalaBot.logger.info(role_ids)
        for role_id in role_ids:

            role: discord.Role = discord.utils.get(ctx.guild.roles, id=role_id)
            if not role:
                KoalaBot.logger.error(f"couldn't find role {role_id} in guild {ctx.guild.id}. Please check.")
            else:
                msg_str += f"{role.mention}\n"
        await ctx.send(msg_str)

    async def prune_rfr_roles(self, guild: discord.Guild):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        rfr_message = self.rfr_database_manager.get_rfr_message(payload.guild_id, payload.channel_id,
                                                                payload.message_id)
        if not rfr_message:
            return
        member_role = self.get_role_member_info(payload.emoji, rfr_message[3], payload.guild_id, payload.channel_id,
                                                payload.message_id, payload.user_id)
        if not member_role:
            return
        await member_role[0].remove_roles(member_role[1])

    async def can_have_rfr_role(self, member: discord.Member) -> bool:
        required_roles: List[int] = self.rfr_database_manager.get_guild_rfr_required_roles(member.guild.id)
        if not required_roles or len(required_roles) == 0:
            return True
        return any(x in required_roles for x in [y.id for y in member.roles])

    async def get_rfr_message_from_prompts(self, ctx: commands.Context) -> Tuple[discord.Message, discord.TextChannel]:
        channel_raw = await self.prompt_for_input(ctx, "Channel name, mention or ID")
        channel: discord.TextChannel = await commands.TextChannelConverter().convert(ctx, channel_raw)
        msg_id = int(await self.prompt_for_input(ctx, "react for role message ID"))
        msg = await ctx.fetch_message(msg_id)
        if not msg:
            raise commands.CommandError("Invalid Message ID given.")
        rfr_msg_row = self.rfr_database_manager.get_rfr_message(ctx.guild.id, channel.id, msg_id)
        if not rfr_msg_row:
            raise commands.CommandError("Message ID given is not that of a react for role message.")
        return msg, channel

    def get_role_member_info(self, emoji_reacted: discord.PartialEmoji, emoji_role_id: int, guild_id: int,
                             channel_id: int, message_id: int, user_id: int) -> Optional[
        Tuple[discord.Member, discord.Role]]:
        if emoji_reacted.is_unicode_emoji():
            rep = emoji.demojize(emoji_reacted.name)
            role_id = self.rfr_database_manager.get_rfr_reaction_role_by_emoji_str(emoji_role_id, rep)
        elif emoji_reacted.is_custom_emoji():
            rep = str(emoji_reacted)
            role_id = self.rfr_database_manager.get_rfr_reaction_role_by_emoji_str(emoji_role_id, rep)
        else:
            KoalaBot.logger.error(
                f"Database error, guild {guild_id} has no entry in rfr database for message_id {message_id} in channel_"
                f"id {channel_id}. Please check this.")
            return
        guild: discord.Guild = self.bot.get_guild(guild_id)
        member: discord.Member = guild.get_member(user_id)
        if not member:
            return
        if not role_id:
            return
        role: discord.Role = discord.utils.get(guild.roles, id=role_id)
        return member, role

    async def parse_emoji_and_role_input_str(self, ctx: commands.Context, input_str: str, remaining_slots: int) -> List[
        Tuple[Union[discord.Emoji, str], discord.Role]]:
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
        rows = input_str.splitlines()
        arr = []
        for row in rows:
            # Try and match it to an raw_emoji first
            raw_emoji = await self.get_first_emoji_from_str(ctx, row.strip())
            if not raw_emoji:
                role = await commands.RoleConverter().convert(ctx, row.strip())
                if not role:
                    await ctx.send(f"DEBUG Couldn't find role {role} from input str {row}")
                else:
                    arr.append(role)
            else:
                arr.append(raw_emoji)
        return arr

    async def prompt_for_input(self, ctx: commands.Context, input_type: str) -> str:
        await ctx.send(f"Please enter {input_type} so I can progress further. I'll wait 60 seconds, don't worry.")
        msg, channel = await self.wait_for_message(self.bot, ctx)
        if not msg:
            await channel.send("Okay, I'll cancel the command.")
        else:
            return msg.content

    async def overwrite_channel_add_reaction_perms(self, guild: discord.Guild, channel: discord.TextChannel):
        roles: List[discord.Role] = guild.roles
        overwrite: discord.PermissionOverwrite = discord.PermissionOverwrite()
        overwrite.update(add_reactions=False)
        for role in roles:
            await channel.set_permissions(role, overwrite=overwrite)
        bot_members: List[discord.Member] = [member for member in guild.members if member.bot]
        for bot in bot_members:
            for role in bot.roles:
                await channel.set_permissions(role, overwrite=None)

    @staticmethod
    async def wait_for_message(bot: discord.Client, ctx: commands.Context, timeout: float = 60.0) -> Tuple[
        Optional[discord.Message], Optional[discord.TextChannel]]:
        try:
            msg = await bot.wait_for('message', timeout=timeout, check=lambda message: message.author == ctx.author)
            return msg, None
        except Exception:
            msg = None
        return msg, ctx.channel

    async def is_user_alive(self, ctx: commands.Context):
        msg = await self.wait_for_message(self.bot, ctx, 10)
        if not msg[0]:
            return False
        return True

    def get_embed_from_message(self, msg: discord.Message) -> Optional[discord.Embed]:
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
        return len(embed.fields)

    async def get_first_emoji_from_str(self, ctx: commands.Context, content: str) -> Optional[
        Union[discord.Emoji, str]]:
        # First check for a custom discord emoji in the string
        await ctx.send(f"DEBUG \\{content}")
        KoalaBot.logger.info(msg=content)
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
        self.database_manager.db_execute_commit(
            f"""INSERT INTO GuildRFRMessages  (guild_id, channel_id, message_id) VALUES ({guild_id}, {channel_id}, {message_id});""")

    def add_rfr_message_emoji_role(self, emoji_role_id: int, emoji_raw: str, role_id: int):
        self.database_manager.db_execute_commit(
            f"""INSERT INTO RFRMessageEmojiRoles (emoji_role_id, emoji_raw, role_id) VALUES ({emoji_role_id}, \"{emoji_raw}\", {role_id});""")

    def remove_rfr_message_emoji_role(self, emoji_role_id: int, emoji_raw: str = None, role_id: int = None):
        if not emoji_raw:
            self.database_manager.db_execute_commit(
                f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND role_id = {role_id};""")
        else:
            self.database_manager.db_execute_commit(
                f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\";""")

    def remove_rfr_message_emoji_roles(self, emoji_role_id: int):
        self.database_manager.db_execute_commit(
            f"""DELETE FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id};""")

    def remove_rfr_message(self, guild_id: int, channel_id: int, message_id: int):
        emoji_role_id = self.get_rfr_message(guild_id, channel_id, message_id)
        if not emoji_role_id:
            return
        else:
            self.remove_rfr_message_emoji_roles(emoji_role_id[3])
        self.database_manager.db_execute_commit(
            f"""DELETE FROM GuildRFRMessages WHERE guild_id = {guild_id} AND channel_id = {channel_id} AND message_id = {message_id};""")

    def get_rfr_message(self, guild_id: int, channel_id: int, message_id: int) -> Optional[Tuple[int, int, int, int]]:
        rows: List[Tuple[int, int, int, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM GuildRFRMessages WHERE guild_id = {guild_id} AND channel_id = {channel_id} AND message_id = {message_id};""")
        if not rows:
            return
        return rows[0]

    def get_guild_rfr_messages(self, guild_id: int):
        rows: List[Tuple[int, int, int, int]] = self.database_manager.db_execute_select(
            "SELECT * FROM GuildRFRMessages WHERE guild_id = ?;", args=[guild_id])
        return rows

    def get_guild_rfr_roles(self, guild_id: int) -> List[int]:
        """
        Returns all role IDs of roles given by RFR messages in a guild

        :param guild_id: Guild ID to check in.
        :return: Role IDs of RFR roles in a specific guild
        :rtype List[int]:
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

        :param emoji_role_id:
        :return:
        """
        rows: List[Tuple[int, str, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id};""")
        if not rows:
            return
        return rows

    def get_rfr_reaction_role(self, emoji_role_id: int, emoji_raw: str, role_id: int):
        """
        Returns a specific emoji-role combo on an rfr message

        :param emoji_role_id:
        :param emoji_raw:
        :param role_id:
        :return:
        """
        rows: List[Tuple[int, str, int]] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\" AND role_id = {role_id};""")
        if not rows:
            return
        return rows[0]

    def get_rfr_reaction_role_by_emoji_str(self, emoji_role_id: int, emoji_raw: str) -> Optional[int]:
        rows: Tuple[int, str, int] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND emoji_raw = \"{emoji_raw}\";""")
        if not rows:
            return
        return rows[0][2]

    def get_rfr_reaction_role_by_role_id(self, emoji_role_id: int, role_id: int) -> Optional[int]:
        rows: Tuple[int, str, int] = self.database_manager.db_execute_select(
            f"""SELECT * FROM RFRMessageEmojiRoles WHERE emoji_role_id = {emoji_role_id} AND role_id = {role_id};""")
        if not rows:
            return
        return rows[0][2]

    def add_guild_rfr_required_role(self, guild_id: int, role_id: int):
        self.database_manager.db_execute_commit("INSERT INTO GuildRFRRequiredRoles VALUES (?,?);",
                                                args=[guild_id, role_id])

    def remove_guild_rfr_required_role(self, guild_id: int, role_id: int):
        self.database_manager.db_execute_commit("DELETE FROM GuildRFRRequiredRoles WHERE guild_id = ? AND role_id = ?",
                                                args=[guild_id, role_id])

    def get_guild_rfr_required_roles(self, guild_id) -> List[int]:
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
