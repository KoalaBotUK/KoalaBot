import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup

import koalabot
from koala.cogs.verification.env import GMAIL_EMAIL, GMAIL_PASSWORD


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

    html = open("koala/cogs/verification/templates/emailtemplate.html").read()
    soup = BeautifulSoup(html, features="html.parser")
    soup.find(id="confirmbuttonbody").string = f"/verify confirm {token}"
    soup.find(id="backup").string = "Main body not loading? Send this command to the bot: " \
                                    f"/verify confirm {token}"

    msg = MIMEMultipart('alternative')
    msg.attach(MIMEText(str(soup), 'html'))
    msg['Subject'] = "Koalabot Verification"
    msg['From'] = username
    msg['To'] = email

    email_server.login(username, password)
    email_server.sendmail(username, [email], msg.as_string())
    email_server.quit()