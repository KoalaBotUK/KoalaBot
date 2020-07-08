import KoalaBot
import discord
from discord.ext import commands
import pytest_mock

def new_discord_activity(activity, name):
    """
    This command takes an activity and name and returns the discord.Activity type for it

    Custom doesn't currently work
    koalabot.uk is added to the end of any activity
    :param activity: The new activity of the bot
    :param name: The name of the activity
    :return:
    """
    name = name + KoalaBot.KOALA_PLUG  # Added to every presence change, do not alter
    lower_activity = str.lower(activity)
    if lower_activity == "playing":
        activity_type = discord.ActivityType.playing
    elif lower_activity == "watching":
        activity_type = discord.ActivityType.watching
    elif lower_activity == "listening":
        activity_type = discord.ActivityType.listening
    elif lower_activity == "streaming":
        return discord.Activity(type=discord.ActivityType.streaming, name=name, url=KoalaBot.STREAMING_URL)
    elif lower_activity == "custom":
        return discord.Activity(type=discord.ActivityType.custom, name=name)
    else:
        raise SyntaxError(f"{activity} is not an activity")
    return discord.Activity(type=activity_type, name=name)

class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.started = False

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ran after all cogs have been started and bot is ready
        :return:
        """
        if not self.started:
            await self.bot.change_presence(activity=new_discord_activity("playing", f"{KoalaBot.COMMAND_PREFIX}help"))
            self.started = True
        print("Bot is ready.")

    @commands.command()
    @commands.check(KoalaBot.is_owner)
    async def change_activity(self, ctx, activity, name):
        """
        Allows admins to change the activity of the bot
        :param ctx: Context of the command
        :param activity: The new activity of the bot
        :param name: The name of the activity
        :return:
        """
        await self.bot.change_presence(activity=new_discord_activity(activity, name))
        if str.lower(activity) in ["playing", "watching", "listening", "streaming"]:
            await ctx.send(f"I am now {activity} {name}")
        else:
            await ctx.send("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        When a member joins console will receive a notification
        :param member: Member that has joined
        :return:
        """
        print(f"{member} has joined the server")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        When a member is removed (kicked or left) console receives a notification
        :param member: Member that has left
        :return:
        """
        print(f"{member} has left the server")

    @commands.command()
    async def ping(self, ctx):
        """
        Returns the ping of the bot
        :param ctx: Context of the command
        :return:
        """
        await ctx.send(f"Pong! {round(self.bot.latency*1000)}ms")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=2):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        :return:
        """
        await ctx.channel.purge(limit=amount)

    @commands.command()
    @commands.is_owner()
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        :return:
        """
        self.bot.load_extension(f'cogs.{extension}')

    @commands.command()
    @commands.is_owner()
    async def unload_cog(self, ctx, extension):
        """
        Unloads a running cog
        :param ctx: Context of the command
        :param extension: The name of the cog
        :return:
        """
        self.bot.unload_extension(f'cogs.{extension}')


def setup(bot: KoalaBot) -> None:
    """Load the Bot cog."""
    bot.add_cog(BaseCog(bot))


