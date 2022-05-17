from sqlalchemy import Column, VARCHAR, ForeignKey

from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class VerifiedEmails:
    __tablename__ = 'verified_emails'
    u_id = Column(DiscordSnowflake, primary_key=True)
    email = Column(VARCHAR(100, collation="utf8_bin"), primary_key=True)

    def __repr__(self):
        return "<verified_emails(%s, %s)>" % \
               (self.u_id, self.email)


@mapper_registry.mapped
class NonVerifiedEmails:
    __tablename__ = 'non_verified_emails'
    u_id = Column(DiscordSnowflake)
    email = Column(VARCHAR(100))
    token = Column(VARCHAR(8), primary_key=True)

    def __repr__(self):
        return "<non_verified_emails(%s, %s, %s)>" % \
               (self.u_id, self.email, self.token)


@mapper_registry.mapped
class Roles:
    __tablename__ = 'roles'
    s_id = Column(DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True)
    r_id = Column(DiscordSnowflake, primary_key=True)
    email_suffix = Column(VARCHAR(100), primary_key=True)

    def __repr__(self):
        return "<roles(%s, %s, %s)>" % \
               (self.s_id, self.r_id, self.email_suffix)


@mapper_registry.mapped
class ToReVerify:
    __tablename__ = 'to_re_verify'
    u_id = Column(DiscordSnowflake, primary_key=True)
    r_id = Column(DiscordSnowflake, primary_key=True)

    def __repr__(self):
        return "<to_re_verify(%s, %s)>" % \
               (self.u_id, self.r_id)
