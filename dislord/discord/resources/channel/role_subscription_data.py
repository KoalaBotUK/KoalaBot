from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class RoleSubscriptionData(ObjDict):
    role_subscription_listing_id = Snowflake
    tier_name: str
    total_months_subscribed = int
    is_renewal = bool

