#   An IRC bot named Flea
#   Copyright (C) 2016  Kris Lamoureux

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>

from core.config import *
import core.irclib as irclib

# Built-in to Python 2.7
import __builtin__
import socket
import ssl
import sys
import os


# Allows reimporting modules
class ImportRollback:
    def __init__(self):
        # Dictionary of loaded modules
        self.curMods = sys.modules.copy()
        self.newImport = __builtin__.__import__

        # Directory of plugins
        self.plugins = os.getcwd()+"/plugins/"

        # Add the plugins location to the path variable
        # Helps the system find the plugin modules
        sys.path.append(self.plugins)

        # Override builtin import function with install()
        __builtin__.__import__ = self.install
        self.newMods = {}

    # Import modules
    def install(self, mod, globals=None, locals=None, fromlist=[]):
        self.newMods[mod] = 1
        return apply(self.newImport, (mod, globals, locals, fromlist))

    # Delete modules
    def reset(self):
        for mod in self.newMods.keys():
            if not self.curMods.has_key(mod):
                del(sys.modules[mod])

        __builtin__.__import__ = self.newImport


def PluginsImport():
    # Get root of Flea
    current = os.getcwd()
    # Path to /plugins/ under /Flea/
    plugins = current+"/plugins/"

    # If /plugins/ exists change directory to it
    if os.path.exists(plugins):
        os.chdir(plugins)

        # Go through every item in /plugins/
        for item in os.listdir(plugins):

            # Only import directory plugins (no single files)
            if os.path.isdir(plugins+item):
                print "[Plugins] Initializing "+item
                __import__(item+".main")

    else:
        return False

    os.chdir(current)
    return True


def main():

    # Parse main settings.conf file
    config = cfgParser("settings.conf")

    # Keep track of modules for a rollback
    importctrl = ImportRollback()

    # Import /plugins/
    if config["plugins"]:
        if not PluginsImport():
            print "[Plugins] Failed to load."

    # Create irclib irc object
    irc = irclib.irc()

    # Set debug to true/false inside irc() object
    irc.debug = config["debug"]

    # Create socket object
    irc.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Wrap socket object to create SSLSocket object
    irc.sock = ssl.wrap_socket(irc.sock)

    # Connect to IRC server
    irc.sock.connect((config["host"], config["port"]))
    print "Connecting to "+config["host"]+':'+str(config["port"])

    # Display SSL information to the user
    ssl_info = irc.sock.cipher()
    if ssl_info != None:
        print "[SSL] Cipher: "+ssl_info[0]
        print "[SSL] Version: "+ssl_info[1]
        print "[SSL] Bits: "+str(ssl_info[2])

    # Send User/Nick message to establish user on the server
    irc.User(config["ident"], config["mode"],
            config["unused"], config["realname"])

    irc.Nick(config["nick"])

    while True:
        # Buffer to store data from server
        data = ''

        while True:
            # Receive data from connection
            tmpdata = irc.sock.recv(4096)
            data = data + tmpdata

            if len(tmpdata) < 4096:
                break

        # If no incoming data exists then connection has closed
        if len(tmpdata) == 0:
            input("Connection closed.")
            sys.exit()

        # Split data to easily deal with it
        data = tmpdata.split("\r\n")

        # Parse IRC line by line
        for line in data:

            # Ignore empty lines
            if len(line) > 0:

                # Print line, parse it and respond
                print line
                pack = irc.Parser(line)

                # Ping Pong, keep the connection alive.
                if pack["cmd"] == "PING":
                    irc.Pong(pack["text"])

                # Send user mode message after command 001
                elif pack["cmd"] == "001":
                    irc.Mode(config["nick"], config["mode"])

                elif pack["cmd"] == "NOTICE":
                    if pack["ident"] == "NickServ":
                        # Send password after NickServ informs you
                        # that your nick is registered
                        pattern = r"[Tt]his nickname is registered"
                        if re.search(pattern, pack["text"]):
                            irc.Identify(config["password"])
                            irc.Join("#Flea")


main()
