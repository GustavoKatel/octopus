#!/usr/bin/python

import os
import signal
import sys
import time
import json
import threading

from node import Node
from interfaces.telegram import Telegram

interface = None
nodes = []
conf = {}

def quit(signum, frame):
    print 'quit'
    interface.stop()

    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)

    nodes = []

    cdir = os.path.dirname(os.path.realpath(__file__))
    conf_file = open(cdir+'/conf/octopus.conf')
    conf = json.load(conf_file)

    for data in conf["nodes"]:
        node = Node(
            data["name"],
            data["username"],
            data["hostname"],
            data["port"],
            conf["auth"]["private_key"]
        )
        nodes.append(node)
        threading.Thread(target = node.connect).start()

    # cli = node.Node("gustavokatel", "127.0.0.1", 22)
    # time.sleep(5)
    # cli.runCommand("touch test.txt && ls")

    interface = Telegram(nodes, conf)
    interface.start()

    while True:
        time.sleep(10)
