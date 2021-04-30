# Fish Store Bot
Fish Store Bot allows choosing products, add to cart and edit it using online buttons. Fish Store Bot interacts with [Moltin CMS](https://www.elasticpath.com/) and use free [Redis database](https://redislabs.com/) to store current state of userorder by chat ID.

Try it, writing to: Telegram channel @fish_store_edu_bot. The Bot is deployed on [Heroku](heroku.com) and is available to test rigth now!

# Demo
![tg_bot_demo](Demo/tg_bot_demo.gif)

# How to install
To customize bots you need some keys that are:
- `TG_TOKEN`: create your own bot writing to BotFather @BotFather,
- `STORE_ID`: store ID of Moltin CMS
Optionally, set `DB_HOST`, `DB_PORT`, `DB_PASSWORD`: get [RedisLabs](https://redislabs.com/) database host, port and password while creating new database. Default values allow to use localhost database.

Python 3 should be already installed. Then use pip3 (or pip) to install dependencies:

```bash
pip3 install -r requirements.txt
```

# How to launch
The Example of launch in Ubuntu is:

```bash
$ python3 tg_bot.py 
```

It is better to launch the script on a remote server, [Heroku](https://devcenter.heroku.com/articles/how-heroku-works), for example. It provides that it will work around the clock. A "Procfile" is need to launch correctly on Heroku.

# Project Goals

The code is written for educational purposes on online-course for web-developers dvmn.org, module [Chat Bots with Python](https://dvmn.org/modules/chat-bots/lesson/support-bot) (project 5, module Chatbots).
