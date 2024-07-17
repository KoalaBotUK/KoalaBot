from dislord import CommandGroup
from kb2.main import client

verify_group = CommandGroup(name="verify", description="Configure Guild Verification")
client.register_group(verify_group)
