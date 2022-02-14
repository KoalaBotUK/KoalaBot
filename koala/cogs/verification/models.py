from sqlalchemy import Column, Integer, String, ForeignKey, orm
from koala.models import mapper_registry
from koala.db import setup


@mapper_registry.mapped
class VerifiedEmails:
    __tablename__ = 'verified_emails'
    u_id = Column(Integer, primary_key=True)
    email = Column(String, primary_key=True)

    def __repr__(self):
        return "<verified_emails(%s, %s)>" % \
               (self.u_id, self.email)


@mapper_registry.mapped
class NonVerifiedEmails:
    __tablename__ = 'non_verified_emails'
    u_id = Column(Integer)
    email = Column(String)
    token = Column(String, primary_key=True)

    def __repr__(self):
        return "<non_verified_emails(%s, %s, %s)>" % \
               (self.u_id, self.email, self.token)


@mapper_registry.mapped
class Roles:
    __tablename__ = 'roles'
    s_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    r_id = Column(Integer, primary_key=True)
    email_suffix = Column(String, primary_key=True)

    def __repr__(self):
        return "<roles(%s, %s, %s)>" % \
               (self.s_id, self.r_id, self.email_suffix)


@mapper_registry.mapped
class ToReVerify:
    __tablename__ = 'to_re_verify'
    u_id = Column(Integer, primary_key=True)
    r_id = Column(String, primary_key=True)

    def __repr__(self):
        return "<to_re_verify(%s, %s)>" % \
               (self.u_id, self.r_id)


setup()
