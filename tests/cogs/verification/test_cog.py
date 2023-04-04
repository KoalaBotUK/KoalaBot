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
import sqlalchemy.orm
from discord.ext import commands
from sqlalchemy import select, delete

# Own modules
import koalabot
from koala.db import session_manager

from koala.cogs import Verification
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, NonVerifiedEmails, Roles, VerifyBlacklist

from tests.log import logger

# Constants
TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'

# Variables


@pytest_asyncio.fixture(autouse=True)
async def cog(bot: commands.Bot):
    cog = Verification(bot)
    await bot.add_cog(cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
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
async def test_enable_verification():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")
        entry = session.execute(select(Roles).filter_by(s_id=guild.id, r_id=role.id)).all()
        assert entry
        session.execute(delete(Roles).filter_by(s_id=guild.id))
        session.commit()


@pytest.mark.asyncio
async def test_disable_verification():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        session.add(Roles(s_id=guild.id, r_id=555, email_suffix="egg.com"))
        session.commit()
        await dpytest.message(koalabot.COMMAND_PREFIX + "removeVerification egg.com testRole")
        assert dpytest.verify().message().content("Emails ending with egg.com no longer give testRole")
        entry = session.execute(select(Roles).filter_by(s_id=guild.id, r_id=role.id)).all()
        assert not entry


@pytest.mark.asyncio
async def test_full_flow():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")

        token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token}", dm)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role in member.roles


@pytest.mark.asyncio
async def test_blacklist():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        await dpytest.message(koalabot.COMMAND_PREFIX + f"verifyBlacklist {member.id} testRole {TEST_EMAIL_DOMAIN}")
        assert dpytest.verify().message().content(
            f"{member} will no longer receive testRole upon verifying with this email suffix")

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")

        token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token}", dm)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role not in member.roles


@pytest.mark.asyncio
async def test_blacklist_remove():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        await dpytest.message(koalabot.COMMAND_PREFIX + f"verifyBlacklist {member.id} testRole {TEST_EMAIL_DOMAIN}")
        assert dpytest.verify().message().content(
            f"{member} will no longer receive testRole upon verifying with this email suffix")

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")

        token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token}", dm)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"verifyBlacklistRemove {member.id} testRole {TEST_EMAIL_DOMAIN}")
        assert dpytest.verify().message().content(
            f"{member} will now be able to receive testRole upon verifying with this email suffix")

        assert role in member.roles


@pytest.mark.asyncio
async def test_verify():
    with session_manager() as session:
        test_config = dpytest.get_config()
        guild = test_config.guilds[0]
        member = guild.members[0]
        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")
        entry = session.execute(select(NonVerifiedEmails).filter_by(u_id=member.id, email=TEST_EMAIL)).all()
        assert entry


@pytest.mark.asyncio
async def test_verify_twice():
    with session_manager() as session:
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

        dm = await member.create_dm()

        msg_mock: discord.Message = dpytest.back.make_message("n", member, dm)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg_mock)):
            await dpytest.message(koalabot.COMMAND_PREFIX + "verify test@egg.com", dm)
        assert dpytest.verify().message().content(
            "This email is already assigned to your account. Would you like to re-verify? (y/n)")
        assert dpytest.verify().message().content(
            "The email will remain registered to the old account.")


@pytest.mark.asyncio
async def test_verify_alternate_account_no():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        member2 = await dpytest.member_join(guild)
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")

        token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token}", dm)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role in member.roles
        assert role not in member2.roles

        dm2 = await member2.create_dm()

        msg_mock: discord.Message = dpytest.back.make_message("n", member2, dm2)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg_mock)):
            await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm2, member2)
        assert dpytest.verify().message().content(
            "This email is already assigned to a different account. Would you like to transfer it to this one? (y/n)")
        assert dpytest.verify().message().content(
            "The email will remain registered to the old account.")


@pytest.mark.asyncio
async def test_verify_alternate_account_yes():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        member2 = await dpytest.member_join(guild)
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
        assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")

        token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

        assert role not in member.roles

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token}", dm)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role in member.roles
        assert role not in member2.roles

        dm2 = await member2.create_dm()

        msg_mock: discord.Message = dpytest.back.make_message("y", member2, dm2)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg_mock)):
            await dpytest.message(koalabot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm2, member2)
        assert dpytest.verify().message().content(
            "This email is already assigned to a different account. Would you like to transfer it to this one? (y/n)")
        assert dpytest.verify().message().content(
            "Please verify yourself using the command you have been emailed")

        assert role not in member.roles

        token2 = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member2.id, email=TEST_EMAIL)).scalar()

        await dpytest.message(koalabot.COMMAND_PREFIX + f"confirm {token2}", dm2, member2)
        assert dpytest.verify().message().content("Your email has been verified, thank you")

        assert role in member2.roles


@pytest.mark.asyncio
async def test_verify_list():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        member = guild.members[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        await dpytest.message(koalabot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} testRole")
        assert dpytest.verify().message().content(
            f"Verification enabled for testRole for emails ending with `{TEST_EMAIL_DOMAIN}`")

        await dpytest.message(koalabot.COMMAND_PREFIX + f"verifyList")

        expected_embeds = discord.Embed(title=f"Current verification setup for {guild.name}")
        expected_embeds.add_field(name=TEST_EMAIL_DOMAIN, value=f"@{role}")

        assert dpytest.verify().message().embed(expected_embeds)




@pytest.mark.asyncio
async def test_confirm():
    with session_manager() as session:
        test_config = dpytest.get_config()
        guild = test_config.guilds[0]
        member = guild.members[0]
        role = dpytest.back.make_role("testRole", guild, id_num=555)
        test_role = Roles(s_id=guild.id, r_id=555, email_suffix="egg.com")
        test_verified_email = NonVerifiedEmails(u_id=member.id, email='test@egg.com', token='testtoken')
        session.add(test_verified_email)
        session.add(test_role)
        session.commit()

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + "confirm testtoken", dm)
        verified = session.execute(select(VerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
        exists = session.execute(select(NonVerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
        assert verified
        assert not exists
        await asyncio.sleep(0.5)
        assert role in member.roles
        assert dpytest.verify().message().content("Your email has been verified, thank you")
        session.delete(test_role)
        session.execute(delete(VerifiedEmails).filter_by(u_id=member.id))
        session.commit()


@pytest.mark.asyncio
async def test_un_verify():
    with session_manager() as session:
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

        dm = await member.create_dm()
        await dpytest.message(koalabot.COMMAND_PREFIX + "unVerify test@egg.com", dm)
        assert dpytest.verify().message().content(
            "test@egg.com has been un-verified and relevant roles have been removed")
        entry = session.execute(select(VerifiedEmails).filter_by(u_id=member.id, email="test@egg.com")).all()
        assert not entry
        assert role not in member.roles
        session.delete(test_role)
        session.commit()


@pytest.mark.asyncio
async def test_get_emails():
    with session_manager() as session:
        test_verified_email = VerifiedEmails(u_id=123, email=TEST_EMAIL)
        session.add(test_verified_email)
        session.commit()
        await dpytest.message(koalabot.COMMAND_PREFIX + "getEmails 123")
        assert dpytest.verify().message().content(f"""This user has registered with:\n{TEST_EMAIL}""")
        session.delete(test_verified_email)
        session.commit()


@pytest.mark.asyncio
async def test_re_verify():
    with session_manager() as session:
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

        await dpytest.message(koalabot.COMMAND_PREFIX + "reVerify <@&555555555555555>")
        assert role not in member.roles
        blacklisted = session.execute(select(ToReVerify).filter_by(u_id=member.id)).all()
        assert blacklisted
        assert dpytest.verify().message().content(
            "That role has now been removed from all users and they will need to re-verify the associated email.")
        session.delete(test_verified_email)
        session.delete(test_role)
        session.execute(delete(ToReVerify).filter_by(u_id=member.id))
        session.commit()

@pytest.mark.asyncio
async def test_re_verify_duplicate():
    with session_manager() as session:
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

        await dpytest.message(koalabot.COMMAND_PREFIX + "reVerify <@&555555555555555>")
        assert role not in member.roles
        blacklisted = session.execute(select(ToReVerify).filter_by(u_id=member.id)).all()
        assert blacklisted
        assert dpytest.verify().message().content(
            "That role has now been removed from all users and they will need to re-verify the associated email.")
        session.delete(test_verified_email)
        session.delete(test_role)
        session.execute(delete(ToReVerify).filter_by(u_id=member.id))
        session.commit()

