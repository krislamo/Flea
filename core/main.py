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
import re


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

    # List of plugins
    plugin_list = []

    # If /plugins/ exists change directory to it
    if os.path.exists(plugins):
        os.chdir(plugins)

        # Go through every item in /plugins/
        for item in os.listdir(plugins):

            # Only import directory plugins (no single files)
            if os.path.isdir(plugins+item):
                print "[Plugins] Initializing "+item
                plugin = __import__(item+".main")
                plugin_list.append(plugin)

    else:
        return False

    os.chdir(current)
    return plugin_list



def main():

    # Create irclib irc object
    irc = irclib.irc()

    # Parse main settings.conf file
    irc.config = cfgParser("settings.conf")

    # Keep track of modules for a rollback
    importctrl = ImportRollback()

    # Import /plugins/
    if irc.config["plugins"]:
        plugins = PluginsImport()
        if not plugins:
            print "[Plugins] Failed to load."

    # Set debug to true/false inside irc() object
    irc.debug = irc.config["debug"]

    # Create socket object
    irc.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Wrap socket object to create SSLSocket object
    irc.sock = ssl.wrap_socket(irc.sock)

    # Connect to IRC server
    irc.sock.connect((irc.config["host"], irc.config["port"]))
    print "Connecting to "+irc.config["host"]+':'+str(irc.config["port"])

    # Display SSL information to the user
    ssl_info = irc.sock.cipher()
    if ssl_info != None:
        print "[SSL] Cipher: "+ssl_info[0]
        print "[SSL] Version: "+ssl_info[1]
        print "[SSL] Bits: "+str(ssl_info[2])

    # Send User/Nick message to establish user on the server
    irc.User(irc.config["ident"], irc.config["mode"],
            irc.config["unused"], irc.config["realname"])

    irc.Nick(irc.config["nick"])

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
                irc.pack = irc.Parser(line)

                # Run all plugins main() function
                if irc.config["plugins"]:
                    for plugin in plugins:
                        plugin.main.main(irc)

                # Ping Pong, keep the connection alive.
                if irc.pack["cmd"] == "PING":
                    irc.Pong(irc.pack["text"])

                # Send user mode message after command 001
                elif irc.pack["cmd"] == "001":
                    irc.Mode(irc.config["nick"], irc.config["mode"])

                elif irc.pack["cmd"] == "NOTICE":
                    if irc.pack["ident"] == "NickServ":
                        # Send password after NickServ informs you
                        # that your nick is registered
                        pattern = r"[Tt]his nickname is registered"
                        if re.search(pattern, irc.pack["text"]):
                            irc.Identify(irc.config["password"])
                            irc.Join(irc.config["channel"])


main()
