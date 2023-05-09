import discord
from discord import app_commands

from koala import env

FAILURE_DESC_ATTR = "koala_check_failure_desc"


def is_owner():
    """
    A command used to check if the user of a command is the owner
    e.g. @checks.is_owner()
    """
    def predicate(interaction: discord.Interaction) -> bool:
        import koalabot
        if env.BOT_OWNER is not None:
            success = interaction.user.id in env.BOT_OWNER
        else:
            success = koalabot.bot.is_owner(interaction.user)
        if not success:
            interaction.data[FAILURE_DESC_ATTR] = "You do not have permission to access this command: not owner"
        return success
    return app_commands.check(predicate)
