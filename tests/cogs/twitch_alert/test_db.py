#!/usr/bin/env python

"""
Testing KoalaBot twitch_alert

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import discord
# Libs
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select, update, insert, delete, and_, or_
from twitchAPI.object import Stream

from koala.cogs.twitch_alert import utils
# Own modules
from koala.cogs.twitch_alert.cog import TwitchAlert
from koala.cogs.twitch_alert.db import TwitchAlertDBManager
from koala.cogs.twitch_alert.models import TwitchAlerts, TeamInTwitchAlert, UserInTwitchTeam, UserInTwitchAlert
from koala.db import session_manager, setup

# Constants
DB_PATH = "Koala.db"


# Variables
