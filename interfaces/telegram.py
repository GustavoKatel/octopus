import telepot
import time
import threading
import re
import os

from node import Status as NodeStatus
from node import Node

class Telegram(threading.Thread):

    def __init__(self, nodes, conf):
        threading.Thread.__init__(self)

        self.running = True
        self.nodes = nodes
        self.conf = conf

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)

        # print msg
        if not msg['from']['username'] in self.conf['telegram']['admins']:
            print "Not authorized: %s" % msg['from']
            self.bot.sendMessage(chat_id, """
-.-.-00-.-.-
>>> OCToPUS <<<<
-.-.-00-.-.-
            """)
            return

        if content_type == 'document':
            doc = msg['document']
            cdir = os.path.dirname(os.path.realpath(__file__))
            print "Downloading... " + doc['file_name']
            fd = open(cdir+'/../data/'+doc['file_name'], 'w')
            self.bot.download_file(doc['file_id'], fd)
            fd.close()

            for node in self.nodes:
                node.putFile(cdir+'/../data/'+doc['file_name'], doc['file_name'])

        elif content_type == 'text':
            text = msg['text']

            # /info
            if re.match(r'/info$', text):
                res = "Nodes list starts -.-.-00-.-.-\n\n"
                for i,node in enumerate(self.nodes):
                    res += str(i) + "- " + str(node) + "\n"
                res += "\nNodes list ends -.-.-00-.-.-\n"
                self.bot.sendMessage(chat_id, res)

            # /info NAME
            elif re.match(r'/info [a-zA-Z0-9_]+', text):
                m = re.match(r'/info ([a-zA-Z0-9_]+)', text)
                name = m.group(1)
                for node in self.nodes:
                    if node.name == name:
                        res = "Node info: %s -.-.-00-.-.-\n\n" % name
                        res += "hostname: %s\n" % node.hostname
                        res += "username: %s\n" % node.username
                        res += "port: %s\n" % node.port
                        res += "status: %s\n" % NodeStatus.toStr(node.status)
                        res += "last command: %s\n" % node.lastCommand
                        res += "current command: %s\n" % node.currentCommand
                        res += "\nNode info ends -.-.-00-.-.-\n"
                        self.bot.sendMessage(chat_id, res)

            # /exec [LIST_OF_NAMES|*] CMD
            elif re.match(r'/exec ([a-zA-Z0-9_,]+|\*) (.+)', text):
                m = re.match(r'/exec ([a-zA-Z0-9_,]+|\*) (.+)', text)
                names = m.group(1)
                cmd = m.group(2)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    node.runCommand(cmd)

            # /connect [LIST_OF_NAMES|*]
            elif re.match(r'/connect ([a-zA-Z0-9_,]+|\*)', text):
                m = re.match(r'/connect ([a-zA-Z0-9_,]+|\*)', text)
                names = m.group(1)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    self.bot.sendMessage(chat_id, "Connecting to: %s -.-.-00-.-.-\n\n" % name)
                    node.connect()

            # /logs [LIST_OF_NAMES|*]
            elif re.match(r'/logs ([a-zA-Z0-9_,]+|\*)', text):
                m = re.match(r'/logs ([a-zA-Z0-9_,]+|\*)', text)
                names = m.group(1)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    cdir = os.path.dirname(os.path.realpath(__file__))
                    f = open(cdir+"/../nodes/"+node.name+".out", "r")

                    res = "Reading logs: %s -.-.-00-.-.-\n\n" % node.name
                    res += ''.join(f.readlines())
                    res += "Reading logs ends: %s -.-.-00-.-.-\n\n" % node.name
                    self.bot.sendMessage(chat_id, res)

                    f.close()

            # /dump [LIST_OF_NAMES|*] [stdout|stderr]
            elif re.match(r'/dump ([a-zA-Z0-9_,]+|\*) (stdout|stderr)', text):
                m = re.match(r'/dump ([a-zA-Z0-9_,]+|\*) (stdout|stderr)', text)
                names = m.group(1)
                dump_type = m.group(2)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    cdir = os.path.dirname(os.path.realpath(__file__))
                    if dump_type == "stdout":
                        f = open(cdir+"/../nodes/"+node.name+".out", "r")
                    else:
                        f = open(cdir+"/../nodes/"+node.name+".err", "r")

                    self.bot.sendDocument(chat_id, f, "%s - %s" % (node.name, dump_type))

            # /download [LIST_OF_NAMES|*] filename
            elif re.match(r'/download ([a-zA-Z0-9_,]+|\*) (.*)', text):
                m = re.match(r'/download ([a-zA-Z0-9_,]+|\*) (.*)', text)
                names = m.group(1)
                filename = m.group(2)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    f = node.getFile(filename)
                    self.bot.sendDocument(chat_id, f, "%s - %s" % (node.name, filename))


            else:
                self.bot.sendMessage(chat_id, self.helpText())

    def stop(self):
        self.running = False

    def run(self):
        self.bot = telepot.Bot(self.conf["telegram"]["token"])
        self.bot.message_loop(self.handle)
        self.running = True

        while self.running:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self.stop()

    def helpText(self):
        return """
-.-.-00-.-.-
>>> OCToPUS <<<<
-.-.-00-.-.-

Commands:
/info: Returns the list of nodes in the server
/info NAME: Returns information about a specif node
/exec LIST_OF_NAMES|* CMD: Execute the command CMD. Eg.: /exec [s1,s2] ls -lah
/connect LIST_OF_NAMES|*: Force a connection to the nodes in LIST_OF_NAMES
/logs LIST_OF_NAMES|*: Read the stdout from the node
/dump LIST_OF_NAMES|* stdout|stderr: Download the stdout or the stderr from a node
/download LIST_OF_NAMES|* FILENAME: Download FILENAME from a node
"""