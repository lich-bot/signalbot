"""Signal bot based on Single-cli."""

import os
import pprint
import json
import time
import docker
import subprocess
import shlex
import logging
import sys
import pika
from distutils.util import strtobool
from message import Message
from botfunctions import SwitchCase
from metadata import version, author

__author__ = author
__version__ = version
SIGNALCLIIMAGE = "pblaas/signalcli:latest"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

if 'REGISTEREDNR' not in os.environ:
    logging.error("Mandatory variable not set: REGISTEREDNR")
    exit(1)
else:
    REGISTEREDNR = os.environ.get('REGISTEREDNR')

if 'DEBUG' in os.environ:
    DEBUG = bool(strtobool(os.environ.get('DEBUG')))
else:
    DEBUG = False

if 'SIGNALEXECUTORLOCAL' in os.environ:
    SIGNALEXECUTORLOCAL = bool(strtobool(os.environ.get('SIGNALEXECUTORLOCAL')))
else:
    SIGNALEXECUTORLOCAL = True

if 'READY' in os.environ:
    READY = bool(strtobool(os.environ.get('READY')))
else:
    READY = False

if 'PRIVATECHAT' in os.environ:
    PRIVATECHAT = bool(strtobool(os.environ.get('PRIVATECHAT')))
else:
    PRIVATECHAT = False

if 'GROUPCHAT' in os.environ:
    GROUPCHAT = bool(strtobool(os.environ.get('GROUPCHAT')))
else:
    GROUPCHAT = True

if 'BLACKLIST' in os.environ:
    blacklist = os.environ.get('BLACKLIST').split(',')
else:
    blacklist = []

if 'WHITELIST' in os.environ:
    whitelist = os.environ.get('WHITELIST').split(',')
else:
    whitelist = []

if 'AMQPSERVERHOST' not in os.environ:
    logging.error("Mandatory variable not set: AMQPSERVERHOST")
    exit(1)
else:
    amqpserverhost = os.environ.get('AMQPSERVERHOST')


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=amqpserverhost))
    channel = connection.channel()

    channel.queue_declare(queue='signalbot')

    def callback(ch, method, properties, body):
        # print(" [x] Received %r" % body)
        parse_message(body)

    channel.basic_consume(queue='signalbot', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def parse_message(value):
    """Create  message object from input."""
    res = json.loads(value)
    if DEBUG:
        pprint.pprint(res)

    # Messages send by the registered number itself.
    if "syncMessage" in res['envelope']:
        if "sentMessage" in res['envelope']['syncMessage']:
            if "groupInfo" in res['envelope']['syncMessage']['sentMessage']:
                messageobject = Message(
                    res['envelope']['source'],
                    res['envelope']['syncMessage']['sentMessage']['message'],
                    res['envelope']['syncMessage']['sentMessage']['groupInfo']['groupId'],
                    res['envelope']['syncMessage']['sentMessage']['timestamp']
                )
                if DEBUG:
                    logging.info(pprint.pprint(res))
                    logging.info(messageobject.getsource())
                    logging.info(messageobject.getgroupinfo())
                    logging.info(messageobject.getmessage())
                if READY:
                    if group_not_in_blacklist(messageobject, blacklist) and group_in_whitelist(messageobject, whitelist):
                        run_signalcli(messageobject)

                    else:
                        logging.info("Group" + messageobject.getgroupinfo() + " is in the blacklist OR not in whitelist.")
                else:
                    logging.info("NOOP due to ready mode set to false.")
            if PRIVATECHAT and "groupInfo" not in res['envelope']['syncMessage']['sentMessage']:
                messageobject = Message(
                    res['envelope']['source'],
                    res['envelope']['syncMessage']['sentMessage']['message'],
                    None,
                    res['envelope']['syncMessage']['sentMessage']['timestamp']
                )
                if DEBUG:
                    logging.info(pprint.pprint(res))
                    logging.info(messageobject.getsource())
                    logging.info(messageobject.getgroupinfo())
                    logging.info(messageobject.getmessage())
                if READY:
                    run_signalcli(messageobject)
                else:
                    logging.info("NOOP due to ready mode set to false.")

    # Messages send by others.
    if "dataMessage" in res['envelope']:
        if "message" in res['envelope']['dataMessage']:
            if "groupInfo" in res['envelope']['dataMessage']:
                messageobject = Message(
                    res['envelope']['source'],
                    res['envelope']['dataMessage']['message'],
                    res['envelope']['dataMessage']['groupInfo']['groupId'],
                    res['envelope']['dataMessage']['timestamp']
                )
                if DEBUG:
                    logging.info(pprint.pprint(res))
                    logging.info(messageobject.getsource())
                    logging.info(messageobject.getgroupinfo())
                    logging.info(messageobject.getmessage())
                if READY:
                    if group_not_in_blacklist(messageobject, blacklist) and group_in_whitelist(messageobject, whitelist):
                        run_signalcli(messageobject)
                    else:
                        logging.info("Group" + messageobject.getgroupinfo() + " is in the blacklist OR not in whitelist.")
                else:
                    logging.info("NOOP due to ready mode set to false.")
            if PRIVATECHAT and "groupInfo" not in res['envelope']['dataMessage']:
                messageobject = Message(
                    res['envelope']['source'],
                    res['envelope']['dataMessage']['message'],
                    None,
                    res['envelope']['dataMessage']['timestamp']
                )
                if DEBUG:
                    logging.info(pprint.pprint(res))
                    logging.info(messageobject.getsource())
                    logging.info(messageobject.getgroupinfo())
                    logging.info(messageobject.getmessage())
                if READY:
                    run_signalcli(messageobject)
                else:
                    logging.info("NOOP due to ready mode set to false.")

def run_signalcli(messageobject):
    """Collect variables which should be passes to the cli send command."""
    global client, home
    if isinstance(messageobject.getmessage(), str) and messageobject.getmessage().startswith('!'):

        action = SwitchCase(__version__, __author__, SIGNALEXECUTORLOCAL, messageobject.getmessage())
        actionmessage = action.switch(messageobject.getmessage()).replace('"', '')

        if not SIGNALEXECUTORLOCAL:
            client = docker.from_env()
            home = os.environ['HOME']
        signal_cli_send(REGISTEREDNR, PRIVATECHAT, GROUPCHAT, SIGNALEXECUTORLOCAL, messageobject, actionmessage)


def signal_cli_send(registerednr, privatechat, groupchat, signalexecutorlocal, messageobject, actionmessage):
    """ Signal CLI command execution"""
    localsignalcli = "/signal/bin/signal-cli --config /config "

    if messageobject.getgroupinfo() is None and privatechat:
        # this is a private one on one chat
        if messageobject.getmessage() == "!gif" and actionmessage == "Gif":
            target_param = " -a " + registerednr + " send " + messageobject.getsource() + " --attachment /tmp/signal/giphy.gif " + " -m "
        elif messageobject.getmessage() == "!xkcd" and actionmessage == "xkcd":
            target_param = " -a " + registerednr + " send " + messageobject.getsource() + " --attachment /tmp/signal/image.png " + " -m "
        elif messageobject.getmessage() == "!me":
            target_param = " -a " + registerednr + " sendReaction " + messageobject.getsource() + " --attachment " + messageobject.getsource() + " -t " + messageobject.gettimestamp() + " -e "
        else:
            target_param = " -a " + registerednr + " send " + messageobject.getsource() + " -m "

        if signalexecutorlocal:
            args = shlex.split(localsignalcli + target_param)
            args.append(actionmessage)
            subprocess.Popen(args)
        else:
            client.containers.run(
                SIGNALCLIIMAGE,
                target_param + "\"" + actionmessage + "\"",
                auto_remove=True,
                volumes={home + '/sender': {'bind': '/config', 'mode': 'rw'},
                         '/tmp/signal': {'bind': '/tmp/signal', 'mode': 'rw'}}
            )
    else:
        if groupchat:
            # this is a group chat
            if messageobject.getmessage() == "!gif" and actionmessage == "Gif":
                target_param = "-a " + registerednr + " send -g " + messageobject.getgroupinfo() + " --attachment /tmp/signal/giphy.gif " + " -m "
            elif messageobject.getmessage() == "!xkcd" and actionmessage == "xkcd":
                target_param = " -a " + registerednr + " send -g " + messageobject.getgroupinfo() + " --attachment /tmp/signal/image.png " + " -m "
            elif messageobject.getmessage() == "!me":
                target_param = " -a " + registerednr + " sendReaction " + "-g " + messageobject.getgroupinfo() + " --attachment " + messageobject.getsource() + " -t " + messageobject.gettimestamp() + " -e "
            elif messageobject.getmessage() == "!rand":
                target_param = " -a " + registerednr + " updateGroup -g " + messageobject.getgroupinfo() + " -n "
            else:
                target_param = " -a " + registerednr + " send -g " + messageobject.getgroupinfo() + " -m "

            if signalexecutorlocal:
                args = shlex.split(localsignalcli + target_param)
                args.append(actionmessage)
                subprocess.Popen(args)
            else:
                client.containers.run(
                    SIGNALCLIIMAGE,
                    target_param + "\"" + actionmessage + "\"",
                    auto_remove=True,
                    volumes={home + '/sender': {'bind': '/config', 'mode': 'rw'},
                             '/tmp/signal': {'bind': '/tmp/signal', 'mode': 'rw'}}
                )


def group_not_in_blacklist(messageobject, blist):
    for groupid in blist:
        if groupid == messageobject.getgroupinfo():
            return False
    return True


def group_in_whitelist(messageobject, wlist):
    if len(wlist) > 0:
        for groupid in wlist:
            if groupid == messageobject.getgroupinfo():
                return True
        return False
    else:
        return True


if __name__ == '__main__':
    try:
        logging.info("Signal bot " + __version__ + " started.")
        logging.info("Debug " + str(DEBUG))
        logging.info("Local Executor " + str(SIGNALEXECUTORLOCAL))
        logging.info("Ready " + str(READY))
        logging.info("Private chat " + str(PRIVATECHAT))
        logging.info("Group Chat " + str(GROUPCHAT))
        logging.info("Blacklists: " + str(blacklist))
        logging.info("Whitelits: " + str(whitelist))
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
