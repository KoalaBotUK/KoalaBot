from . import api, cog


def setup(bot):
    cog.setup(bot)
    api.setup(bot)
