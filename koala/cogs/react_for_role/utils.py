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

# Own modules

# Libs

# Constants

UNICODE_DISCORD_EMOJI_REGEXP: re.Pattern = re.compile(r"^:(\w+):$")
CUSTOM_EMOJI_REGEXP: re.Pattern = re.compile(r"^<a?:(\w+):(\d+)>$")
UNICODE_EMOJI_REGEXP: re.Pattern = re.compile(emoji.get_emoji_regexp())
IMAGE_FORMATS = ("image/png", "image/jpeg", "image/gif")
