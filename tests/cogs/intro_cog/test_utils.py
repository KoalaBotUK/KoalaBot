#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest

# Own modules
from koala.cogs.intro_cog.utils import ask_for_confirmation, confirm_message, dm_group_message


@pytest.mark.parametrize("msg_content, is_invalid, expected",
                         [('y', False, True), ('n', False, False), ('Y', False, True), ('N', False, False),
                          ('x', True, False), (' ', True, False), ('', True, False), ('yy', True, False)])
@pytest.mark.asyncio
async def test_ask_for_confirmation(msg_content, is_invalid, expected):
    author = dpytest.get_config().members[0]
    channel = dpytest.get_config().channels[0]
    message = dpytest.back.make_message(author=author, content=msg_content, channel=channel)
    x = await ask_for_confirmation(message, channel)
    assert x == expected
    if is_invalid:
        assert dpytest.verify().message()


@pytest.mark.parametrize("msg_content, expected",
                         [('y', True), ('n', False), ('Y', True), ('N', False), ('', None), (' ', None),
                          ('y ', True), (' n', False)])
@pytest.mark.asyncio
async def test_confirm_message(msg_content, expected):
    author = dpytest.get_config().members[0]
    channel = dpytest.get_config().channels[0]
    message = dpytest.back.make_message(author=author, content=msg_content, channel=channel)
    x = await confirm_message(message)
    assert x is expected

@pytest.mark.asyncio
async def test_dm_single_group_message():
    test_message = 'default message'
    test_member = dpytest.get_config().members[0]
    x = await dm_group_message([test_member], test_message)
    assert dpytest.verify().message().content(test_message)
    assert x == 1


@pytest.mark.asyncio
async def test_dm_plural_group_message():
    test_message = 'default message'
    test_member = dpytest.get_config().members[0]
    test_member_2 = await dpytest.member_join()
    await dpytest.empty_queue()
    x = await dm_group_message([test_member, test_member_2], test_message)
    assert dpytest.verify().message().content(test_message)
    assert dpytest.verify().message().content(test_message)
    assert x == 2


@pytest.mark.asyncio
async def test_dm_empty_group_message():
    test_message = 'this should not be sent'
    x = await dm_group_message([], test_message)
    assert dpytest.verify().message().nothing()
    assert x == 0
