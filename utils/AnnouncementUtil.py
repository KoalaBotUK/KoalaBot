import asyncio
import discord
from discord.ext import commands
from utils.KoalaUtils import extract_id
from utils import KoalaColours


class AnnounceManager:
    """
        The manager that handles the messages under the commands
    """

    def __init__(self, bot):
        """
        Initiate a manager for the announcement section
        :param bot:The bot that is used for this function
        """
        self.bot = bot
        self.active_messages = {}
        self.roles = {}

    def has_active_msg(self, id):
        """
        Check if a particular id has an active announcement pending announcement
        :param id: The id of the author of the command
        :return: Boolean of whether there is an active announcement or not
        """
        return id in self.active_messages.keys() and self.active_messages[id] is not None

    def get_msg(self, ctx):
        """
        A function to get the announcement
        :param ctx: The context of the bot
        :return: The message related to the current context's author
        """
        return self.active_messages[ctx.author.id]

    def get_roles(self, ctx):
        """
        A function to get the roles the announcement will be sent to
        :param ctx: The context of the bot
        :return: All the roles that are tagged
        """
        temp = []
        for role in self.roles[ctx.author.id]:
            temp.append(discord.utils.get(ctx.guild.roles,id=role))
        return temp

    def get_role_names(self, ctx):
        """
        A function to get the names of all the roles the announcement will be sent to
        :param ctx: The context of the bot
        :return: All the names of the roles that are tagged
        """
        temp = []
        for role in self.get_roles(ctx):
            temp.append(role.name)
        return temp

    def get_receivers(self, ctx):
        """
        A function to get the receivers of a particular announcement
        :param ctx: The context of the bot
        :return: All the receivers of the announcement
        """
        temp = []
        for role in self.get_roles(ctx):
            temp += role.members
        return list(set(temp))

    def receiver_msg(self, ctx):
        """
        A function to create a string message about receivers
        :param ctx: The context of the bot
        :return: A string message about receivers
        """
        if not self.roles[ctx.author.id]:
            return f"You are currently sending to Everyone and there are {str(len(ctx.guild.members))} receivers"
        return f"You are currently sending to {self.get_role_names(ctx)} and there are {str(len(self.get_receivers(ctx)))} receivers"

    def construct_embed(self, ctx):
        """
        Constructing an embedded message from the information stored in the manager
        :param ctx: The context of the bot
        :return: An embedded message for the announcement
        """
        message = self.get_msg(ctx)
        embed: discord.Embed = discord.Embed(title=message.title,
                                             description=message.description, colour=KoalaColours.KOALA_GREEN)
        embed.set_thumbnail(url=message.thumbnail)
        return embed

    async def create_msg(self, ctx: commands.Context):
        """
        Creating a new announcement
        :param ctx: The context of the bot
        :return:
        """
        await ctx.send("Please enter a message")
        message = await self.bot.wait_for("message")
        if len(message.content) > 2000:
            await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
            return
        self.active_messages[ctx.author.id] = AnnounceMessage(f"This announcement is from {ctx.guild.name}",
                                                              message.content,
                                                              ctx.guild.icon_url)
        self.roles[ctx.author.id] = []
        await ctx.send(embed=self.construct_embed(ctx))

    async def preview(self, ctx):
        """
        Preview the announcement by displaying a embedded message
        :param ctx: The context of the bot
        """
        await ctx.send(embed=self.construct_embed(ctx))

    async def change_title(self, ctx: commands.Context):
        """
        Changing the title of an existing announcement
        :param ctx: The context of the bot
        """
        await self.preview(ctx)
        await ctx.send("Please enter the new title")
        title = await self.bot.wait_for("message")
        self.get_msg(ctx).set_title(title.content)
        await self.preview(ctx)

    async def change_content(self, ctx: commands.Context):
        """
        Changing the content of an existing announcement
        :param ctx: The context of the bot
        """
        await self.preview(ctx)
        await ctx.send("Please enter the new message")
        message = await self.bot.wait_for("message")
        if len(message.content) > 2000:
            await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
            return
        self.get_msg(ctx).set_description(message)
        await self.preview(ctx)

    async def add_roles(self, ctx: commands.Context):
        """
        Adding a list of roles to the existing roles
        :param ctx: The context of the bot
        """
        await ctx.send(self.receiver_msg(ctx))
        await ctx.send("Please enter the roles you want to tag separated by space")
        message = await self.bot.wait_for("message")
        for new_role in message.content.split():
            id = extract_id(new_role)
            if id not in self.roles[ctx.author.id]:
                self.roles[ctx.author.id].append(id)
        await ctx.send(self.receiver_msg(ctx))

    async def remove_roles(self, ctx: commands.Context):
        """
        Removing a list of roles from the existing roles
        :param ctx: The context of the bot
        """
        await ctx.send(self.receiver_msg(ctx))
        await ctx.send("Please enter the roles you want to remove separated by space")
        message = await self.bot.wait_for("message")
        for new_role in message.content.split():
            id = extract_id(new_role)
            if id in self.roles[ctx.author.id]:
                self.roles[ctx.author.id].remove(id)
        await ctx.send(self.receiver_msg(ctx))

    async def send_msg(self, ctx: commands.Context):
        """
        Sending the announcement to the receivers
        :param ctx: The context of the bot
        """
        embed = self.construct_embed(ctx)
        if self.roles[ctx.author.id]:
            for receiver in self.get_receivers(ctx):
                await receiver.send(embed=embed)
        else:
            for receiver in ctx.guild.members:
                await receiver.send(embed=embed)
        self.active_messages[ctx.author.id] = None
        self.roles[ctx.author.id] = []
        await ctx.send("The announcement was made successfully")

    async def cancel_msg(self, ctx: commands.Context):
        """
        Cancelling an existing announcement
        :param ctx: The context of the bot
        """
        self.active_messages[ctx.author.id] = None
        self.roles[ctx.author.id] = []
        await ctx.send("The current announcement has been cancelled")


class AnnounceMessage:
    """
    A class consisting the information about a announcement message
    """
    def __init__(self, title, message, thumbnail):
        """
        Initiate the message with default thumbnail, title and description
        :param title: The title of the announcement
        :param message: The message included in the announcement
        :param thumbnail: The logo of the server
        """
        self.title = title
        self.description = message
        self.thumbnail = thumbnail

    def set_title(self, title):
        """
        Changing the title of the announcement
        :param title: A string consisting the title
        :return:
        """
        self.title = title

    def set_description(self, message):
        """
        Changing the message in the announcement
        :param message: A string consisting the message
        :return:
        """
        self.description = message

    def set_thumbnail(self, thumbnail):
        """
        Changing the thumbnail picture of the announcement
        :param thumbnail: A url to the picture
        :return:
        """
        self.thumbnail = thumbnail
