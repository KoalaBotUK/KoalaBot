import discord.ext.test as dpytest
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select, delete

from koala.cogs.verification import db
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, NonVerifiedEmails, Roles

from koala.cogs import Verification
from tests.log import logger

# Constants
TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'

@pytest_asyncio.fixture(autouse=True)
async def cog(bot: commands.Bot):
    cog = Verification(bot)
    await bot.add_cog(cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return cog

@pytest.mark.asyncio
async def test_get_member_join_emails(session):

    # setting up the fake guild and roles
    test_config = dpytest.get_config()
    guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
    test_config.guilds.append(guild)
    dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
    session.add(test_role)
    session.commit()

    # set up member
    await dpytest.member_join(1)

    results = db.get_potential_emails(guild.members[0])

    assert results[0].r_id == 555
    assert results[0].email_suffix == 'koalabot.uk'

    # clean up 
    session.delete(test_role)
    session.commit()


@pytest.mark.asyncio
# this feels SO redundant, hopefully i'm doing this right
async def test_member_join_email_results(session):

    # setting up the fake guild and roles
    test_config = dpytest.get_config()
    guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
    test_config.guilds.append(guild)
    dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
    session.add(test_role)
    session.commit()

    await dpytest.member_join(1)

    test_verified = VerifiedEmails(u_id=guild.members[0].id, email=TEST_EMAIL)
    session.add(test_verified)
    session.commit()

    # actual code test
    results = db.member_join_email_results(guild.members[0], TEST_EMAIL_DOMAIN)

    assert results[0][0].u_id == guild.members[0].id
    assert results[0][0].email == TEST_EMAIL

    # clean up 
    session.delete(test_role)
    session.delete(test_verified)
    session.commit()


@pytest.mark.asyncio
async def test_member_blacklisted(session):
    # setting up the fake guild and roles
    test_config = dpytest.get_config()
    guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
    test_config.guilds.append(guild)
    dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
    session.add(test_role)
    session.commit()

    await dpytest.member_join(1)

    test_reverify = ToReVerify(u_id=guild.members[0].id, r_id=555)
    session.add(test_reverify)
    session.commit()

    # actual code test
    results = db.member_join_blacklisted(guild.members[0], 555)

    assert results[0][0].u_id == guild.members[0].id
    assert results[0][0].r_id == '555'

    # clean up 
    session.delete(test_role)
    session.delete(test_reverify)
    session.commit()