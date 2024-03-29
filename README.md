# SignalBot
![alt text](coverage.svg "Code coverage")


## Create intial config
```
mkdir $HOME/signal
docker run -v $HOME/signal:/config --rm -it pblaas/signalcli:latest link
```


Paste entire tsdevice:/? string in https://www.nayuki.io/page/qr-code-generator-library and read with Signal APP to add connected device.

## Start messaging
After device is connected you can start sending messages:
```
docker run -v $HOME/signal:/config --rm -it pblaas/signalcli:latest -u YOURREGISTEREDNR send RECEIVER -m "your message"
```


## show CLI help
```
docker run -v $HOME/signal:/config --rm -it pblaas/signalcli:latest -h
```

## having some fun
```
echo `curl --silent https://api.chucknorris.io/jokes/random | jq '. | .value'` | docker run -v $HOME/signal:/config --rm -i signal:dev -u +316 send --g "2SExxxxxxxx"
```

## bot ideas
* !chuck - show random chuck norris joke [DONE] [API]
* !gif  - show random gif from Giphy [DONE] [API] [APIKEY]
* !weather - show weather 
* !flip - Flip a coin heads or tails [DONE]
* <del> !gnews - parse latest news from gnews API. [DONE] [API] [APIKEY] </del> [DEPRECATED]
* !me - return with random reply [DONE]
* !version - show version [DONE]
* !help - show available commands [DONE]
* !haiku - show japanese poem [DONE]
* !names - random names based on python haikunator implementation [DONE]
* !launch - return lanched message and send source a image of impact.
* !trivia - return trivia questions [DONE] [API]
* !twitch - Return twitch and game related info [DONE] [API] [OAUTH2]
* !bored - Returns random activities [DONE]  [API]
* !dog - Return short message with Emoji [DONE] 
* !winamp - Returns winamp slogan with Emoji [DONE]
* !hn - Returns random hacker news [DONE] [API]
* !xkcd - Returns random image from xkcd [DONE] [API]
* !tmdb - Return movie and tv series information from The Movie DB. [DONE] [API] [APIKEY]

https://www.webfx.com/tools/emoji-cheat-sheet/


# How to use this Signal Bot?

This bot is based on Signal CLI. https://github.com/AsamK/signal-cli.

The bot can run in two modes. 
* local executor mode
* non-local executor mode

## Dependencies
* Signal APP (when linking)
* Docker engine
* $HOME/signal directory which contains Signal user profile.
* Giphy.com API key
* Gnews API key
* Twitch clientid and clientsecret


### Docker engine

The bot implementation relies heavilly on container technology. The bot can be run inside of a container or outside of a container. When using the bot outside of a container it will still make calls to container image pblaas/signalcli for the response messages. More on this is explained in local or non-local executor mode.

The containers expect signal user profile configuration in /config. So when containers are started a volume mapping is mandatory.
`-v $HOME/signal:/config`


### Local executor mode

Local executor means the bot will run inside of a docker container and will also use the signal-cli command from inside of the container. 

Local executor mode is the default and expects the bot to run inside a container.
There are two mandatory variables which need to be set in order for the bot to work.

*   REGISTEREDNR - contains the phone number you registered with the Signal  messenger service.
*   READY - Default set to False. In order for the Bot to respond it needs to be set to True.


To start the bot run:
```
docker run -v $HOME/signal:/config -e REGISTEREDNR="+31_YOUR_NUMBER" --rm -it pblaas/signalbot
```

To enable to bot to reply to commands like !help
```
docker run -v $HOME/signal:/config -e READY=True -e REGISTEREDNR="+31_YOUR_NUMBER" --rm -it pblaas/signalbot
```

### Non-local executor mode

The non local executor mode means the bot can be run in local python3 environment with all the requirements from requirements.txt installed. It will however use a docker container to fire response commands. 

To set non-local executor mode change the environment variable:
`export SIGNALEXECUTORLOCAL=False`

Just like the local executor mode you also need to set some mandatory flags in order for the bot
to be useful.

*   REGISTEREDNR - contains the phone number you registered with the Signal  messenger service.
*   READY - Default set to False. In order for the Bot to respond it needs to be set to True.


To start the bot run:
```
pip3 install -r requirements
python signalbot/
```

## Linking or registering

The first step into using this app is making sure Signal CLI has a proper user profile. This profile will be stored in a directory for example called 'signal'

### Linking

To start a linking process with Signal CLI one should provide the link flag to signal-cli
```
signal-cli link
```

This will reveil a link string which looks like 'tsdevice:/?'. Copy this entire string into this page https://www.nayuki.io/page/qr-code-generator-library which will dynamicly create a QR code.
Use your Signal APP e.g on your phone to add additional devices by scanning the QR code.

### Registering

If you are not linking the bot to an existing account you can register the bot with the register flag.
```
signal-cli -u YOURPHONENUMBER register
```

You will then receive a SMS message with validation code.
```
signal-cli -u YOURPHONENUMBER verify CODE
```

# Development

Additional bot functions should be added to the signalbot/functions directory. The modules should contain a class
and one or multiple methods. The class then should also be added to the __init__.py file in the functions directory.

Next the new class should be added to the SwitchCase class in botfunctions.py so its content can be inherited. 
Reviewing some existing functions should give a good idea on how the bot can be extended.


Testcases are written in Pytest and utilize a .env file with the required variables:
```
READY=False
DEBUG=True
SIGNALEXECUTORLOCAL=False
PRIVATECHAT=False
GROUPCHAT=True
REGISTEREDNR="+316"
GIPHY_APIKEY=""
GNEWS_APIKEY=""
TMDB_APIKEY=""
TWITCH_CLIENTID=""
BLACKLIST=""
WHITELIST=""
```
## Running the Pytest testsuite
```
pytest signalbot/
```
## Run Pytest code coverage check
```
pytest --cov-report html:cov_html --cov=signalbot signalbot/
```
