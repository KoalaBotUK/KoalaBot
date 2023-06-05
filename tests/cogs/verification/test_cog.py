#!/usr/bin/env python
# TODO Test rig broken, restart from beginning and fix.
"""
Testing KoalaBot Verification
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select, delete

# Own modules
import koalabot
from koala.cogs import Verification
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, NonVerifiedEmails, Roles, VerifyBlacklist
from koala.db import session_manager
from tests.log import logger

# Constants
TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'

# Variables


@pytest_asyncio.fixture(name='verify_cog', scope='function', autouse=True)
async def verify_cog_fixture(bot: commands.Bot):
    """ setup any state specific to the execution of the given module."""
    cog = Verification(bot)
    await bot.add_cog(cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return cog


@pytest.fixture(autouse=True)
def delete_tables(session):
    session.execute(delete(VerifiedEmails))
    session.execute(delete(ToReVerify))
    session.execute(delete(NonVerifiedEmails))
    session.execute(delete(Roles))
    session.execute(delete(VerifyBlacklist))
    session.commit()


@pytest.mark.asyncio
async def test_member_join_no_verify():
    await dpytest.member_join()
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_member_join_verif_enabled():
    with session_manager() as session:
        test_config = dpytest.get_config()
        guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
        test_config.guilds.append(guild)
        dpytest.back.make_role("testRole", guild, id_num=555)
        test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
        session.add(test_role)
        session.commit()
        welcome_message = f"""Welcome to testMemberJoin. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using `{koalabot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers.
`{TEST_EMAIL_DOMAIN}` for `@testRole`"""
        await dpytest.member_join(1)
        await asyncio.sleep(0.25)
        assert dpytest.verify().message().content(welcome_message)
        session.delete(test_role)
        session.commit()


@pytest.mark.asyncio
async def test_member_join_already_verified(bot: commands.Bot):
    with session_manager() as session:
        guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
        bot._connection._guilds[guild.id] = guild

        test_user = dpytest.back.make_user("TestUser", 1234, id_num=999)
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        test_verified_email = VerifiedEmails(u_id=999, email=f'egg@{TEST_EMAIL_DOMAIN}')
        test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
        session.add(test_verified_email)
        session.add(test_role)
        session.commit()

        await dpytest.member_join(guild, test_user)
        await asyncio.sleep(0.25)
        welcome_message = f"""Welcome to testMemberJoin. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using `{koalabot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers.
`{TEST_EMAIL_DOMAIN}` for `@testRole`"""
        assert dpytest.verify().message().content(welcome_message)
        member = guild.get_member(test_user.id)
        assert role in member.roles

        session.delete(test_verified_email)
        session.delete(test_role)
        session.commit()


@pytest.mark.asyncio
async def test_enable_verification(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)

    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

    entry = session.execute(select(Roles).filter_by(s_id=guild.id, r_id=role.id)).all()
    assert entry
    session.execute(delete(Roles).filter_by(s_id=guild.id))
    session.commit()


@pytest.mark.asyncio
async def test_disable_verification(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    session.add(Roles(s_id=guild.id, r_id=555, email_suffix=TEST_EMAIL_DOMAIN))
    session.commit()

    await verify_cog.disable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Emails ending with `{TEST_EMAIL_DOMAIN}` no longer give testRole")

    entry = session.execute(select(Roles).filter_by(s_id=guild.id, r_id=role.id)).all()
    assert not entry


# how to defer?
@pytest.mark.asyncio
async def test_full_flow(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
        
    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert role not in member.roles

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role in member.roles


@pytest.mark.asyncio
async def test_blacklist(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")
    
    await verify_cog.blacklist.callback(verify_cog, mock_interaction, member, role, TEST_EMAIL_DOMAIN)
    mock_interaction.response.assert_eq(f"{member} will no longer receive testRole upon verifying with this email suffix")

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert role not in member.roles

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role not in member.roles


@pytest.mark.asyncio
async def test_blacklist_remove(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")
    
    await verify_cog.blacklist.callback(verify_cog, mock_interaction, member, role, TEST_EMAIL_DOMAIN)
    mock_interaction.response.assert_eq(f"{member} will no longer receive testRole upon verifying with this email suffix")

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert role not in member.roles

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role not in member.roles
    
    await verify_cog.blacklist_remove.callback(verify_cog, mock_interaction, member, role.id, TEST_EMAIL_DOMAIN)
    mock_interaction.response.assert_eq(f"{member} will be able to receive testRole upon verifying with this email suffix")

    assert role in member.roles


@pytest.mark.asyncio
async def test_verify(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    member = guild.members[0]

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    entry = session.execute(select(NonVerifiedEmails).filter_by(u_id=member.id, email=TEST_EMAIL)).all()
    assert entry


@pytest.mark.asyncio
async def test_verify_twice(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    channel = guild.channels[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    test_verified_email = VerifiedEmails(u_id=member.id, email='test@egg.com')
    test_role = Roles(s_id=guild.id, r_id=role.id, email_suffix='egg.com')
    session.add(test_verified_email)
    session.add(test_role)
    session.commit()

    msg_mock: discord.Message = dpytest.back.make_message("n", member, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await verify_cog.verify.callback(verify_cog, mock_interaction, "test@egg.com")
    assert dpytest.verify().message().content(
        "This email is already assigned to your account. Would you like to verify anyway? (y/n)")
    assert dpytest.verify().message().content("Okay, you will not be verified with test@egg.com")


@pytest.mark.asyncio
async def test_verify_alternate_account_no(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    channel = guild.channels[0]
    member = guild.members[0]
    member2 = await dpytest.member_join(guild)
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert role not in member.roles

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role in member.roles
    assert role not in member2.roles

    msg_mock: discord.Message = dpytest.back.make_message("n", member2, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)

    mock_interaction.response.assert_eq("This email is already assigned to a different account. Would you like to verify anyway? (y/n)")
    mock_interaction.response.assert_eq(f"Okay, you will not be verified with {TEST_EMAIL}")


@pytest.mark.asyncio
async def test_verify_alternate_account_yes(verify_cog: Verification, mock_interaction, session):
    config = dpytest.get_config()
    guild = config.guilds[0]
    channel = guild.channels[0]
    member = guild.members[0]
    member2 = await dpytest.member_join(guild)
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

    await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)
    mock_interaction.response.assert_eq("Please verify yourself using `/verify confirm` and the token you have been emailed")

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert role not in member.roles

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role in member.roles
    assert role not in member2.roles

    msg_mock: discord.Message = dpytest.back.make_message("n", member2, channel)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=msg_mock)):
        await verify_cog.verify.callback(verify_cog, mock_interaction, TEST_EMAIL)

    mock_interaction.response.assert_eq("This email is already assigned to a different account. Would you like to verify anyway? (y/n)")
    mock_interaction.response.assert_eq(f"Okay, please wait")

    assert role not in member.roles

    token2 = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member2.id, email=TEST_EMAIL)).scalar()

    await verify_cog.confirm.callback(verify_cog, mock_interaction, token2)
    mock_interaction.response.assert_eq("Your email has been verified, thank you")

    assert role in member2.roles


@pytest.mark.asyncio
async def test_verify_list(verify_cog: Verification, mock_interaction):
    config = dpytest.get_config()
    guild = config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)

    await verify_cog.enable_verification.callback(verify_cog, mock_interaction, TEST_EMAIL_DOMAIN, role)
    mock_interaction.response.assert_eq(f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")
    
    await verify_cog.check_verifications.callback(verify_cog, mock_interaction)

    expected_embeds = discord.Embed(title=f"Current verification setup for {guild.name}")
    expected_embeds.add_field(name=TEST_EMAIL_DOMAIN, value=f"@{role}")

    mock_interaction.response.assert_eq(embed=expected_embeds)


@pytest.mark.asyncio
async def test_confirm(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=guild.id, r_id=555, email_suffix="egg.com")
    test_verified_email = NonVerifiedEmails(u_id=member.id, email='test@egg.com', token='testtoken')
    session.add(test_verified_email)
    session.add(test_role)
    session.commit()

    await verify_cog.confirm.callback(verify_cog, mock_interaction, "testtoken")
    verified = session.execute(select(VerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
    exists = session.execute(select(NonVerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
    assert verified
    assert not exists
    await asyncio.sleep(0.5)
    assert role in member.roles
    mock_interaction.response.assert_eq("Your email has been verified, thank you")
    session.delete(test_role)
    session.execute(delete(VerifiedEmails).filter_by(u_id=member.id))
    session.commit()


@pytest.mark.asyncio
async def test_un_verify(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    test_verified_email = VerifiedEmails(u_id=member.id, email='test@egg.com')
    test_role = Roles(s_id=guild.id, r_id=role.id, email_suffix='egg.com')
    session.add(test_verified_email)
    session.add(test_role)
    session.commit()

    await verify_cog.un_verify.callback(verify_cog, mock_interaction, "test@egg.com")
    mock_interaction.response.assert_eq("test@egg.com has been un-verified and relevant roles have been removed")
    entry = session.execute(select(VerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
    assert not entry
    assert role not in member.roles
    session.delete(test_role)
    session.commit()


@pytest.mark.asyncio
async def test_get_emails(verify_cog: Verification, mock_interaction, session):
    test_verified_email = VerifiedEmails(u_id=123, email=TEST_EMAIL)
    session.add(test_verified_email)
    session.commit()
    await verify_cog.get_emails.callback(verify_cog, mock_interaction, 123)
    mock_interaction.response.assert_eq(f"""This user has registered with:\n{TEST_EMAIL}""", ephemeral=True)
    session.delete(test_verified_email)
    session.commit()


@pytest.mark.asyncio
async def test_re_verify(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555555555555555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    test_verified_email = VerifiedEmails(u_id=member.id, email='test@egg.com')
    test_role = Roles(s_id=guild.id, r_id=role.id, email_suffix='egg.com')
    session.add(test_verified_email)
    session.add(test_role)
    session.commit()

    await verify_cog.re_verify.callback(verify_cog, mock_interaction, role)
    assert role not in member.roles
    blacklisted = session.execute(select(ToReVerify).filter_by(u_id=member.id)).all()
    assert blacklisted
    mock_interaction.response.assert_eq("That role has now been removed from all users and they will need to re-verify the associated email.")
    session.delete(test_verified_email)
    session.delete(test_role)
    session.execute(delete(ToReVerify).filter_by(u_id=member.id))
    session.commit()

@pytest.mark.asyncio
async def test_re_verify_duplicate(verify_cog: Verification, mock_interaction, session):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555555555555555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    test_verified_email = VerifiedEmails(u_id=member.id, email='test@egg.com')
    test_role = Roles(s_id=guild.id, r_id=role.id, email_suffix='egg.com')
    test_re_verify = ToReVerify(u_id=member.id, r_id=role.id)
    session.add(test_verified_email)
    session.add(test_role)
    session.add(test_re_verify)
    session.commit()

    await verify_cog.re_verify.callback(verify_cog, mock_interaction, role)
    assert role not in member.roles
    blacklisted = session.execute(select(ToReVerify).filter_by(u_id=member.id)).all()
    assert blacklisted
    mock_interaction.response.assert_eq("That role has now been removed from all users and they will need to re-verify the associated email.")
    session.delete(test_verified_email)
    session.delete(test_role)
    session.execute(delete(ToReVerify).filter_by(u_id=member.id))
    session.commit()

