# Built-in/Generic Imports
import random
import smtplib
import string
from email.message import EmailMessage

# Libs
import discord
from discord.ext import commands
import sqlalchemy.orm
from sqlalchemy import select, delete, and_, text

# Own modules
import koalabot
from koala.db import assign_session, session_manager, insert_extension
from .env import GMAIL_EMAIL, GMAIL_PASSWORD
from .log import logger
from .models import VerifiedEmails, NonVerifiedEmails, Roles, ToReVerify


# Constants

# Variables

def send_email(email, token):
    """
    Sends an email through gmails smtp server from the email stored in the environment variables
    :param email: target to send an email to
    :param token: the token the recipient will need to verify with
    :return:
    """
    email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    email_server.ehlo()
    username = GMAIL_EMAIL
    password = GMAIL_PASSWORD

    msg = EmailMessage()
    msg.set_content(f"Please send the bot the command:\n\n{koalabot.COMMAND_PREFIX}confirm {token}")
    msg['Subject'] = "Koalabot Verification"
    msg['From'] = username
    msg['To'] = email

    email_server.login(username, password)
    email_server.send_message(msg)
    email_server.quit()

@assign_session
def enable_verification(guild_id, guild_roles, session: sqlalchemy.orm.Session, suffix=None, role=None):
    """
    Set up a role and email pair for KoalaBot to verify users with
    :param guild_id: guild id of current guild
    :param guild_roles: all enabled roles in the current guild
    :param session:
    :param suffix: end of the email (e.g. "example.com")
    :param role: the role to give users with that email verified (e.g. @students)
    :return:
    """
    if not role or not suffix:
        raise InvalidArgumentError(f"Please provide the correct arguments\n(`{koalabot.COMMAND_PREFIX}enable_verification <domain> <@role>`")

    try:
        role_id = int(role[3:-1])
    except ValueError:
        raise InvalidArgumentError("Please give a role by @mentioning it")
    except TypeError:
        raise InvalidArgumentError("Please give a role by @mentioning it")

    role_valid = discord.utils.get(guild_roles, id=role_id)
    if not role_valid:
        raise InvalidArgumentError("Please mention a role in this guild")

    exists = session.execute(select(Roles)
                                .filter_by(s_id=guild_id, r_id=role_id, email_suffix=suffix)).all()
    if exists:
        raise VerifyError("Verification is already enabled for that role")

    session.add(Roles(s_id=guild_id, r_id=role_id, email_suffix=suffix))
    session.commit()

    return role_valid

@assign_session
def disable_verification(guild_id, session: sqlalchemy.orm.Session, suffix=None, role=None):
    """
    Disable an existing verification listener
    :param guild_id: guild id of current guild
    :param suffix: end of the email (e.g. "example.com")
    :param role: the role paired with the email (e.g. @students)
    :return:
    """
    if not role or not suffix:
        raise InvalidArgumentError(
            f"Please provide the correct arguments\n(`{koalabot.COMMAND_PREFIX}enable_verification <domain> <@role>`")

    try:
        role_id = int(role[3:-1])
    except ValueError:
        raise InvalidArgumentError("Please give a role by @mentioning it")
    except TypeError:
        raise InvalidArgumentError("Please give a role by @mentioning it")

    session.execute(delete(Roles).filter_by(s_id=guild_id, r_id=role_id, email_suffix=suffix))
    session.commit()

@assign_session
def verify(user_id, email, session: sqlalchemy.orm.Session):
    """
    Send to KoalaBot in dms to verify an email with our system
    :param user_id: id of user to be verified
    :param email: the email you want to verify
    :return:
    """
    already_verified = session.execute(select(VerifiedEmails).filter_by(email=email)).all()

    in_blacklist = session.execute(select(ToReVerify).filter_by(u_id=user_id)).all()

    if already_verified and not in_blacklist:
        raise VerifyError("That email is already verified")

    verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
    session.add(NonVerifiedEmails(u_id=user_id, email=email, token=verification_code))
    session.commit()

    send_email(email, verification_code)

@assign_session
def un_verify(user_id, email, session: sqlalchemy.orm.Session):
    """
    Send to KoalaBot in dms to un-verify an email with our system
    :param user_id: id of user to be un-verified
    :param email: the email you want to un-verify
    :return:
    """
    entry = session.execute(select(VerifiedEmails).filter_by(u_id=user_id, email=email)).all()

    if not entry:
        raise VerifyError("You have not verified that email")

    session.execute(delete(VerifiedEmails).filter_by(u_id=user_id, email=email))
    session.commit()

@assign_session
def confirm(user_id, token, session: sqlalchemy.orm.Session):
    """
    Send to KoalaBot in dms to confirm the verification of an email
    :param ctx: the context of the discord message
    :param token: the token emailed to you to verify with
    :return:
    """
    entry = session.execute(select(NonVerifiedEmails).filter_by(token=token)).scalar()

    if not entry:
        raise InvalidArgumentError("That is not a valid token")

    already_verified = session.execute(select(VerifiedEmails)
                                        .filter_by(u_id=user_id, email=entry.email)).all()

    if not already_verified:
        session.add(VerifiedEmails(u_id=user_id, email=entry.email))

    session.execute(delete(NonVerifiedEmails).filter_by(token=token))

    potential_roles = session.execute(select(Roles.r_id)
                                        .where(text(":email like ('%' || email_suffix)")),
                                        {"email": entry.email}).all()
    if potential_roles:
        for role_id in potential_roles:
            session.execute(delete(ToReVerify).filter_by(r_id=role_id[0], u_id=user_id))

    session.commit()

    return entry

@assign_session
def get_emails(user_id: int, session: sqlalchemy.orm.Session):
    """
    See the emails a user is verified with
    :param user_id: the id of the user who's emails you want to find
    :return: string of emails user is verified with
    """
    results = session.execute(select(VerifiedEmails.email).filter_by(u_id=user_id)).all()

    return '\n'.join([x[0] for x in results])

@assign_session
async def re_verify(role, guild_id, guild_roles, guild_members, session: sqlalchemy.orm.Session):
    """
    Removes a role from all users who have it and marks them as needing to re-verify before giving it back
    :param role: the role to be removed and re-verified (e.g. @students)
    :param guild_id: the guild to re-verify for
    :param guild_roles: all roles active in the current guild
    :param guild_members: all members in the current guild
    :return:
    """
    try:
        role_id = int(role[3:-1])
    except ValueError:
        raise InvalidArgumentError("Please give a role by @mentioning it")
    except TypeError:
        raise InvalidArgumentError("Please give a role by @mentioning it")

    exists = session.execute(select(Roles).filter_by(s_id=guild_id, r_id=role_id)).all()

    if not exists:
        raise VerifyError("Verification is not enabled for that role")
    role = discord.utils.get(guild_roles, id=role_id)
    for member in guild_members:
        if role in member.roles:
            await member.remove_roles(role)
            session.add(ToReVerify(u_id=member.id, r_id=role.id))

    session.commit()

@assign_session
def assign_roles_on_startup(bot, session: sqlalchemy.orm.Session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)).all()
    for g_id, r_id, suffix in results:
        try:
            guild = bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            assign_role_to_guild(guild, role, suffix)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)

@assign_session
def assign_roles_for_user(bot, user_id, email, session: sqlalchemy.orm.Session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                                .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

    for g_id, r_id, suffix in results:
        blacklisted = session.execute(select(ToReVerify).filter_by(r_id=r_id, u_id=user_id)).all()

        if blacklisted:
            continue
        try:
            guild = bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            if not member:
                member = guild.fetch_member(user_id)
            member.add_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)
        except discord.errors.NotFound:
            logger.warn(f"user with id {user_id} not found")

@assign_session
def remove_roles_for_user(bot, user_id, email, session: sqlalchemy.orm.Session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                                .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

    for g_id, r_id, suffix in results:
        try:
            guild = bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            if not member:
                member = guild.fetch_member(user_id)
            member.remove_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)
        except discord.errors.NotFound:
            logger.error(f"user with id {user_id} not found in {guild}")

@assign_session
def assign_role_to_guild(guild, role, suffix, session: sqlalchemy.orm.Session):
    results = session.execute(select(VerifiedEmails.u_id).where(VerifiedEmails.email.endswith(suffix))).all()

    for user_id in results:
        try:
            blacklisted = session.execute(select(ToReVerify).filter_by(r_id=role.id, u_id=user_id[0])).all()

            if blacklisted:
                continue
            member = guild.get_member(user_id[0])
            if not member:
                member = guild.fetch_member(user_id[0])
            member.add_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)
        except discord.errors.NotFound:
            logger.error(f"user with id {user_id} not found in {guild}")

class InvalidArgumentError(Exception):
    pass

class VerifyError(Exception):
    pass