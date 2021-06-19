# KoalaBot
[![Discord Server](https://img.shields.io/discord/729325378681962576.svg?style=flat-square&logo=discord&logoColor=white&labelColor=697EC4&color=7289DA&label=%20)](https://discord.gg/5etEjVd)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/KoalaBotUK/KoalaBot/CI?label=tests&style=flat-square)](https://github.com/KoalaBotUK/KoalaBot/actions/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/KoalaBotUK/KoalaBot.svg?style=flat-square)](https://lgtm.com/projects/g/KoalaBotUK/KoalaBot/context:python)

KoalaBot is a free open source discord bot being developed by students from around the UK. 
Our aim is to ensure university society committee leaders can access all they need and from one easy to use discord bot 
to improve their server and society! 

## Authors

* **Jack Draper** - *Project Manager* - [JayDwee](https://github.com/JayDwee)
* **Stefan Cooper** - *Senior Developer* - [stefan-cooper](https://github.com/stefan-cooper)
* **Kieran Allinson** - *Senior Developer* - [Kaspiaan](https://github.com/Kaspiaan)
* **Viraj Shah** - *Senior Developer* - [VirajShah18](https://github.com/VirajShah18)

All of our other amazing developers can be seen on our website https://koalabot.uk

See also the list of [current developers](https://github.com/orgs/KoalaBotUK/teams/developers) who are actively participating in this project.

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
ENCRIPTION = False # or True (default) for disabling/enabling the database encryption
SQLITE_KEY = 123EXAMPLE456ENCRYPTION789KEY0 # A custom SQLcipher key

# Twitch Alert (Required for TwitchAlert Extension)
TWITCH_TOKEN = tw1tch70k3n # Twitch Token taken from the twitch developers portal
TWITCH_SECRET = tw1tch53cr3t # Twitch Secret taken from the twitch developers portal

# Verification (Required for Verify Extension)
GMAIL_EMAIL = example@gmail.com # email for a gmail account
GMAIL_PASSWORD = example_password123 # password for the same gmail account
```
`DISCORD_TOKEN` is the only required environment variable for KoalaBot to be run.

## Running the tests
Tests are run using the pytest library
```bash
$ pytest
```

## Running KoalaBot
If all prerequisites have been followed, you can start KoalaBot with the following command
```bash
$ python3 KoalaBot.py
```

## Links
* Website & Dashboard: [koalabot.uk](https://koalabot.uk)
* Support Discord: [discord.koalabot.uk](https://discord.koalabot.uk)
* Development Documentation: [documents.koalabot.uk](https://documents.koalabot.uk)
* Developer Roadmap: [development.koalabot.uk](https://development.koalabot.uk)
* Twitter: [twitter.com/KoalaBotUK](https://twitter.com/KoalaBotUK)
