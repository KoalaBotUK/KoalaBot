# Own imports
import koalabot
from announce_message import AnnounceMessage, Announce, announce_is_enabled

def announce_is_enabled(guild):
    return announce_is_enabled(guild)

def not_exceeded_limit(self, guild_id, ctx):
    """
    Check if the number of announcements in the guild is not exceeded
    :param guild_id: The id of the guild
    :param ctx: The context of the message
    :return: True if the number of announcements is not exceeded, False otherwise
    """
    try:
        result = self.Announce.not_exceeded_limit(guild_id, ctx)
    except PermissionError:
        result = False

    ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))

def has_active_msg(self, guild_id, ctx):
    """
    Check if there is an active announcement message
    :param guild_id: The id of the guild
    :param ctx: The context of the message
    :return: True if there is an active announcement message, False otherwise
    """
    try:
        result = self.Announce.has_active_msg(guild_id, ctx)
    except PermissionError:
        result = False

    ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))

def get_role_names(self, guild_id, roles, ctx):
    """
    Get the names of the roles
    :param guild_id: The id of the guild
    :param roles: The roles
    :param ctx: The context of the message
    :return: A string consisting the names of the roles
    """
    try:
        result = self.Announce.get_role_names(guild_id, roles, ctx)
    except PermissionError:
        result = False

    ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))

def get_receivers(self, guild_id, roles, ctx):
    """
    Get the receivers of the announcement
    :param guild_id: The id of the guild
    :param roles: The roles
    :param ctx: The context of the message
    :return: A list of the receivers
    """
    try:
        result = self.Announce.get_receivers(guild_id, roles, ctx)
    except PermissionError:
        result = False

    ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))

def receiver_msg(self, guild, ctx):
        """
        A function to create a string message about receivers
        :param guild: The guild of the bot
        :return: A string message about receivers
        """
        try:
            result = self.Announce.receiver_msg(guild, ctx)
        except PermissionError:
            result = False

        ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))

def construct_embed(self, guild: discord.Guild, ctx):
    """
    Construct an embed message
    :param guild: The guild of the bot
    :param ctx: The context of the message
    :return: An embed message
    """
    try:
        result = self.Announce.construct_embed(guild, ctx)
    except PermissionError:
        result = False

    ctx.send(result or (str(ctx.guild) == koalabot.TEST_USER and koalabot.is_dpytest))
    
    @commands.check(announce_is_enabled)
    @commands.group(name="announce")
    async def announce(self, ctx):
        """
        Use k!announce create to create an announcement
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{koalabot.COMMAND_PREFIX}help announce` for more information")

    @commands.check(announce_is_enabled)
    @announce.command(name="create")
    async def create(self, ctx):
        """
        Create a new message that will be available for sending
        :param ctx: The context of the bot
        :return:
        """
        if not self.not_exceeded_limit(ctx.guild.id):
            remaining_days = math.ceil(
                ANNOUNCE_SEPARATION_DAYS - ((int(time.time()) - self.announce_database_manager.get_last_use_date(
                    ctx.guild.id)) / SECONDS_IN_A_DAY))
            await ctx.send("You have recently sent an announcement and cannot use this function for " + str(
                remaining_days) + " days")
            return
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("There is currently an active announcement being created, you can use 'k!announce cancel' "
                           "or 'k!announce send' to complete it")
        else:
            await ctx.send("Please enter a message, I'll wait for 60 seconds, no rush.")
            message, channel = await wait_for_message(self.bot, ctx)
            if not message:
                await channel.send("Okay, I'll cancel the command.")
                return
            if len(message.content) > MAX_MESSAGE_LENGTH:
                await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
                return
            self.messages[ctx.guild.id] = AnnounceMessage(f"",
                                                          message.content,
                                                          ctx.guild.icon_url)
            self.roles[ctx.guild.id] = []
            await ctx.send(f"An announcement has been created for guild {ctx.guild.name}")
            await ctx.send(embed=self.construct_embed(ctx.guild))
            await ctx.send(self.receiver_msg(ctx.guild))

    @commands.check(announce_is_enabled)
    @announce.command(name="changeTitle")
    async def change_title(self, ctx):
        """
        Change the title of the embedded message
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the new title, I'll wait for 60 seconds, no rush.")
            title, channel = await wait_for_message(self.bot, ctx)
            if not title:
                await channel.send("Okay, I'll cancel the command.")
                return
            self.messages[ctx.guild.id].set_title(title.content)
            await ctx.send(embed=self.construct_embed(ctx.guild))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="changeContent")
    async def change_content(self, ctx):
        """
        Change the content of the embedded message
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the new message, I'll wait for 60 seconds, no rush.")
            message, channel = await wait_for_message(self.bot, ctx)
            if not message:
                await channel.send("Okay, I'll cancel the command.")
                return
            if len(message.content) > MAX_MESSAGE_LENGTH:
                await ctx.send("The content is more than 2000 characters long, and exceeds the limit")
                return
            self.messages[ctx.guild.id].set_description(message.content)
            await ctx.send(embed=self.construct_embed(ctx.guild))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="addRole", aliases=["add"])
    async def add_role(self, ctx):
        """
        Add a role to list of people to send the announcement to
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the roles you want to tag separated by space, I'll wait for 60 seconds, no rush.")
            message, channel = await wait_for_message(self.bot, ctx)
            if not message:
                await channel.send("Okay, I'll cancel the command.")
                return
            for new_role in message.content.split():
                role_id = extract_id(new_role)
                if role_id not in self.roles[ctx.guild.id] and discord.utils.get(ctx.guild.roles,
                                                                                 id=role_id) is not None:
                    self.roles[ctx.guild.id].append(role_id)
            await ctx.send(self.receiver_msg(ctx.guild))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="removeRole", aliases=["remove"])
    async def remove_role(self, ctx):
        """
        Remove a role from a list of people to send the announcement to
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send("Please enter the roles you want to remove separated by space, I'll wait for 60 seconds, no rush.")
            message, channel = await wait_for_message(self.bot, ctx)
            if not message:
                await channel.send("Okay, I'll cancel the command.")
                return
            for new_role in message.content.split():
                role_id = extract_id(new_role)
                if role_id in self.roles[ctx.guild.id]:
                    self.roles[ctx.guild.id].remove(role_id)
            await ctx.send(self.receiver_msg(ctx.guild))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="preview")
    async def preview(self, ctx):
        """
        Post a constructed embedded message to the channel where the command is invoked
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            await ctx.send(embed=self.construct_embed(ctx.guild))
            await ctx.send(self.receiver_msg(ctx.guild))
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="send")
    async def send(self, ctx):
        """
        Send a pending announcement
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            embed = self.construct_embed(ctx.guild)
            if self.roles[ctx.guild.id]:
                for receiver in self.get_receivers(ctx.guild.id, ctx.guild.roles):
                    try:
                        await receiver.send(embed=embed)
                    except (discord.Forbidden, AttributeError, discord.HTTPException) as e:
                        logger.error(f'User {receiver.id} cannot recieve dms')
            else:
                for receiver in ctx.guild.members:
                    try:
                        await receiver.send(embed=embed)
                    except (discord.Forbidden, AttributeError, discord.HTTPException) as e:
                        logger.error(f'User {receiver.id} cannot recieve dms')

            self.messages.pop(ctx.guild.id)
            self.roles.pop(ctx.guild.id)
            self.announce_database_manager.set_last_use_date(ctx.guild.id, int(time.time()))
            await ctx.send("The announcement was made successfully")
        else:
            await ctx.send("There is currently no active announcement")

    @commands.check(announce_is_enabled)
    @announce.command(name="cancel")
    async def cancel(self, ctx):
        """
        Cancel a pending announcement
        :param ctx: The context of the bot
        :return:
        """
        if self.has_active_msg(ctx.guild.id):
            self.messages.pop(ctx.guild.id)
            self.roles.pop(ctx.guild.id)
            await ctx.send("The announcement was cancelled successfully")
        else:
            await ctx.send("There is currently no active announcement")


def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Announce(bot))
    logger.info("announce is ready.")
