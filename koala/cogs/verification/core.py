# Built-in/Generic Imports
import random
import smtplib
import string
from email.message import EmailMessage

# Libs
import discord
from discord.ext import commands
from sqlalchemy import select, delete, and_, text

# Own modules
import koalabot
from koala.db import session_manager, insert_extension
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

def enable_verification(guild_id, guild_roles, suffix=None, role=None):
    """
    Set up a role and email pair for KoalaBot to verify users with
    :param guild_id: guild id of current guild
    :param guild_roles: all enabled roles in the current guild
    :param suffix: end of the email (e.g. "example.com")
    :param role: the role to give users with that email verified (e.g. @students)
    :return:
    """
    with session_manager() as session:
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

def disable_verification(guild_id, suffix=None, role=None):
    """
    Disable an existing verification listener
    :param guild_id: guild id of current guild
    :param suffix: end of the email (e.g. "example.com")
    :param role: the role paired with the email (e.g. @students)
    :return:
    """
    with session_manager() as session:
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

def verify(user_id, email):
    """
    Send to KoalaBot in dms to verify an email with our system
    :param user_id: id of user to be verified
    :param email: the email you want to verify
    :return:
    """
    with session_manager() as session:
        already_verified = session.execute(select(VerifiedEmails).filter_by(email=email)).all()

        in_blacklist = session.execute(select(ToReVerify).filter_by(u_id=user_id)).all()

        if already_verified and not in_blacklist:
            raise VerifyError("That email is already verified")

        verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        session.add(NonVerifiedEmails(u_id=user_id, email=email, token=verification_code))
        session.commit()

        send_email(email, verification_code)

def un_verify(user_id, email):
    """
    Send to KoalaBot in dms to un-verify an email with our system
    :param user_id: id of user to be un-verified
    :param email: the email you want to un-verify
    :return:
    """
    with session_manager() as session:
        entry = session.execute(select(VerifiedEmails).filter_by(u_id=user_id, email=email)).all()

        if not entry:
            raise VerifyError("You have not verified that email")

        session.execute(delete(VerifiedEmails).filter_by(u_id=user_id, email=email))
        session.commit()


class InvalidArgumentError(Exception):
    pass

class VerifyError(Exception):
    pass