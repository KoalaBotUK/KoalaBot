# KoalaBot
[![Discord Server](https://img.shields.io/discord/729325378681962576.svg?style=flat-square&logo=discord&logoColor=white&labelColor=697EC4&color=7289DA&label=%20)](https://discord.gg/5etEjVd)
[![CI](https://github.com/KoalaBotUK/KoalaBot/actions/workflows/ci.yml/badge.svg)](https://github.com/KoalaBotUK/KoalaBot/actions/workflows/ci.yml)
[![CodeQL](https://github.com/KoalaBotUK/KoalaBot/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/KoalaBotUK/KoalaBot/actions/workflows/codeql-analysis.yml)
![Codecov](https://img.shields.io/codecov/c/github/KoalaBotUK/KoalaBot?style=flat-square)


KoalaBot is a free open source discord bot being developed by students from around the UK. 
Our aim is to ensure university society committee leaders can access all they need and from one easy to use discord bot 
to improve their server and society! 

## Developers

* **Jack Draper** - *Project Manager* - [JayDwee](https://github.com/JayDwee)
* **Stefan Cooper** - *Senior Developer* - [stefan-cooper](https://github.com/stefan-cooper)
* **Viraj Shah** - *Senior Developer* - [VirajShah18](https://github.com/VirajShah18)
* **Otto Hooper** - *Senior Developer* - [VottonDev](https://github.com/VottonDev)
* **Zoe Tam** - *Senior Developer* - [abluey](https://github.com/abluey)

All of our other amazing developers can be seen on our website https://koalabot.uk

See also the list of [contributors](https://github.com/KoalaBotUK/KoalaBot/graphs/contributors) to this repo.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This application uses python 3.8 which you can download [here](https://www.python.org/downloads/)

All python packages you need can be found in the [requirements.txt](requirements.txt).
Before running the bot you must install these as so:

```bash
$ pip3 install -r requirements.txt
``` 

#### Linux
On linux, database encryption will be enabled. Therefore, further packages are needed.
```bash
$ sudo apt install libsqlcipher-dev
```

### Environment Variables

Before running the bot you will need to create a `.env` file in the root directory of this project. A template for this can be found here:

```dotenv
# Discord Bot
DISCORD_TOKEN = AdiSc0RdT0k3N # A discord Token taken from the discord developers portal 
BOT_OWNER = 123456789 # (optional) A discord ID for the person who should have access to owner commands (will default to bot owner)

# Encryption (optional)
ENCRYPTED = False # or True (default) for disabling/enabling the database encryption
SQLITE_KEY = 123EXAMPLE456ENCRYPTION789KEY0 # A custom SQLcipher key
CONFIG_PATH = ./config # directory of logs and database (default=./config)

# Twitch Alert (Required for TwitchAlert Extension)
TWITCH_TOKEN = tw1tch70k3n # Twitch Token taken from the twitch developers portal
TWITCH_SECRET = tw1tch53cr3t # Twitch Secret taken from the twitch developers portal

# Verification (Required for Verify Extension)
GMAIL_EMAIL = example@gmail.com # email for a gmail account
GMAIL_PASSWORD = example_password123 # password for the same gmail account

# API
API_PORT = 8080 # port for the API to listen on (default=8080)
```

```
`DISCORD_TOKEN` is the only required environment variable for KoalaBot to be run.

## Running the tests
Tests are run using the pytest library
```bash
$ pytest tests
```

## Running KoalaBot
If all prerequisites have been followed, you can start KoalaBot with the following command
```bash
$ python3 koalabot.py
```

## Running KoalaBot with Docker
Here are some example snippets to help you get started creating a container.

### docker-compose (recommended, [click here for more info](https://docs.linuxserver.io/general/docker-compose))
```yaml
---
version: "3.9"
services:
  transmission:
    image: jaydwee/koalabot
    container_name: KoalaBot
    environment:
      - DISCORD_TOKEN = bot_token
      - BOT_OWNER = owner_user_id #optional
      - ENCRYPTED = boolean #optional
      - SQLITE_KEY = key #optional
      - TWITCH_TOKEN = twitch_application_token #optional (TwitchAlert)
      - TWITCH_SECRET = twitch_application_secret #optional (TwitchAlert)
      - GMAIL_EMAIL = example@gmail.com #optional (Verify)
      - GMAIL_PASSWORD = example_password123 #optional (Verify)
    ports:
      - "8080:8080"
    volumes:
      - <path to data>:/config
    restart: unless-stopped
```

### docker cli ([click here for more info](https://docs.docker.com/engine/reference/commandline/cli/))

```bash
docker run \
  --name=Koala \
  -e DISCORD_TOKEN=bot_token \
  -e BOT_OWNER=owner_user_id `#optional` \
  -e ENCRYPTED=boolean `#optional` \
  -e SQLITE_KEY=key `#optional` \
  -e TWITCH_TOKEN=twitch_application_token `#optional (TwitchAlert)` \
  -e TWITCH_SECRET=twitch_application_secret `#optional (TwitchAlert)` \
  -e GMAIL_EMAIL=example@gmail.com `#optional (Verify)` \
  -e GMAIL_PASSWORD=example_password123 `#optional (Verify)` \
  -p 8080:8080
  -v <path to data>:/config \
  --restart unless-stopped \
  jaydwee/koalabot
```

### Using Env File
Add `--env-file .env` to your command

### Versions
`jaydwee/koalabot:latest` The latest stable release\
`jaydwee/koalabot:prerelease` The latest prerelease\
`jaydwee/koalabot:master` The current state of the master branch\
`jaydwee/koalabot:v<x.y.z>` The specified version of KoalaBot

## Links
* Website & Dashboard: [koalabot.uk](https://koalabot.uk)
* Support Discord: [discord.koalabot.uk](https://discord.koalabot.uk)
* Development Documentation: [documents.koalabot.uk](https://documents.koalabot.uk)
* Developer Roadmap: [development.koalabot.uk](https://development.koalabot.uk)
* Twitter: [twitter.com/KoalaBotUK](https://twitter.com/KoalaBotUK)
