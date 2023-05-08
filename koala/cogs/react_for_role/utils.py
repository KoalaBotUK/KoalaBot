#!/usr/bin/env python

"""
KoalaBot Reaction Roles Code

Author: Anan Venkatesh
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import re

import emoji
import flag

# Own modules

# Libs

# Constants

UNICODE_DISCORD_EMOJI_REGEXP: re.Pattern = re.compile(r"^:(\w+):$")
CUSTOM_EMOJI_REGEXP: re.Pattern = re.compile(r"^<a?:(\w+):(\d+)>$")
UNICODE_EMOJI_REGEXP: re.Pattern = re.compile(emoji.get_emoji_regexp())
FLAG_EMOJI_REGEXP: re.Pattern = re.compile("([\U0001F1E6-\U0001F1FF]+)", flags=re.UNICODE)
IMAGE_FORMATS = ("image/png", "image/jpeg", "image/gif")
