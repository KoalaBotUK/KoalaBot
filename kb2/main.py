import os

import dislord

PUBLIC_KEY = os.environ.get("PUBLIC_KEY")
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")

client = dislord.ApplicationClient(PUBLIC_KEY, BOT_TOKEN)

def serverless_handler(event, context):  # Not needed if using server
    return client.serverless_handler(event, context)


def sync_serverless_handler(event, context):
    client.sync_commands()
    client.sync_commands(guild_ids=[g.id for g in client.guilds])
    return {"statusCode": 200}


if __name__ == '__main__':  # Not needed if using serverless
    client.sync_commands()
    client.sync_commands(guild_ids=[g.id for g in client.guilds])
    dislord.server.start_server(client, host='0.0.0.0', debug=True, port=8123)
