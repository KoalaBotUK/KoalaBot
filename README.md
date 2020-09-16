# KoalaBot
[![Discord Server](https://img.shields.io/discord/523301176309972993.svg?label=Support_Discord)](https://discord.gg/5etEjVd)

KoalaBot is a free open source discord bot being developed by students from around the UK. 
Our aim is to ensure university society committee leaders can access all they need and from one easy to use discord bot 
to improve their server and society! 

## Authors

* **Jack Draper** - *Project Manager* - [JayDwee](https://github.com/JayDwee)
* **Kieran Allinson** - *Project Lead: Backend* - [Kaspiaan](https://github.com/Kaspiaan)
* **Viraj Shah** - *Project Lead: Frontend* - [VirajShah18](https://github.com/VirajShah18)


* **Anan Venkatesh** - *Developer* - [Unknownlocal](https://github.com/Unknownlocal)
* **Harry Nelson** - *Developer* - [largereptile](https://github.com/largereptile)
* **Robert Slawik** - *Developer* - [RobertSlawik](https://github.com/RobertSlawik)
* **Rurda Malik** - *Developer* - [BlahBlahRudra](https://github.com/BlahBlahRudra)
* **Josh Jones** - *Developer* - 

See also the list of [contributors](https://github.com/KoalaBotUK/KoalaBot/graphs/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This application uses python 3.8 which you can download [here](https://www.python.org/downloads/)

All python packages you need can be found in the [requirements.txt](requirements.txt).
Before running the bot you must install these as so:

```
pip3 install -r requirements.txt
``` 


### Environment Variables

Before running the bot you will need to create a `.env` file in the root directory of this project. A template for this can be found here:

```python
# Discord Bot
DISCORD_TOKEN = AdiSc0RdT0k3N # A discord Token taken from the discord developers portal 
BOT_OWNER = 123456789 # A discord ID for the person who should have access to owner commands


# Twitch Alert
TWITCH_TOKEN = tw1tch70k3n # Twitch Token taken from the twitch developers portal
TWITCH_SECRET = tw1tch53cr3t # Twitch Secret taken from the twitch developers portal

# Verification
GMAIL_EMAIL = example@gmail.com # email for a gmail account
GMAIL_PASSWORD = example_password123 # password for the same gmail account
```

## Running the tests

Due to the incompatibility of the `discord.py 1.4` with our testing library `dpytest` you will need to download an
older version of discord.py for testing.
```
pip3 install dpytest==0.0.20
pip3 install discord.py==1.3.4
```

Tests are run using `pytest`
```
python3 -m pytest tests/
```

## Links
* Website & Dashboard: [koalabot.uk](http://koalabot.uk)
* Support Discord: [discord.koalabot.uk](http://discord.koalabot.uk)
* Development Documentation: [documents.koalabot.uk](http://documents.koalabot.uk)
* Developer Roadmap: [development.koalabot.uk](http://development.koalabot.uk)
* Twitter: [twitter.com/KoalaBotUK](https://twitter.com/KoalaBotUK)