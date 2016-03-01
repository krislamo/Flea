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
    def __init__(self, plugins_folder="/plugins"):
        # Dictionary of loaded modules
        self.curMods = sys.modules.copy()
        self.newImport = __builtin__.__import__

        self.plugins = os.path.join(os.getcwd(), plugins_folder)

        # Add the plugins location to the path variable
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


# Print and log to logfile
def printlog(message, log=None):
    print message
    if log is not None:
        log.write(message+"\n")


def PluginsImport(log=None, plugins_folder="/plugins"):
    plugins = os.path.join(os.getcwd(), plugins_folder)
    plugin_list = []

    if os.path.exists(plugins):
        os.chdir(plugins)

        for item in os.listdir(plugins):
            if os.path.isdir(os.path.join(plugins, item)):
                printlog("[Plugins] Initializing " + item, log)
                plugin = __import__(item+".main")
                plugin_list.append(plugin)

    else:
        return None

    os.chdir(os.getcwd())
    return plugin_list


def init_connection(config_file="settings.conf"):
    irc_conn = irclib.irc()
    irc_conn.config = cfgParser(config_file)

    if irc_conn.config["logging"]:
        log = open("log.txt", 'a')
        irc_conn.log = log
    else:
        log = None

    irc_conn.debug = irc_conn.config["debug"]

    # Keep track of modules for a rollback
    importctrl = ImportRollback()

    # Import /plugins
    if irc_conn.config["plugins"]:
        plugins = PluginsImport(log)
    else:
        plugins = None

    if plugins is not None:
        # TODO: Add more debugging messages, sporadatic.
        printlog("[Plugins] Failed to load.", log)

    # Create socket object and wrap with SSL object, then connect.
    irc_conn.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_conn.sock = ssl.wrap_socket(irc_conn.sock)

    server = (irc_conn.config["host"], irc_conn.config["port"])
    try:
        printlog("Connecting to " + server[0] + ':' + str(server[1]))
        irc_conn.sock.connect(server[0], server[1])
    except:
        printlog("Connection failed.", log)
        return (None, None)

    # Display SSL inforation to the user
    ssl_info = irc_conn.sock.cipher()
    if ssl_info is not None:
        printlog("[SSL] Cipher: " + ssl_info[0], log)
        printlog("[SSL] Version: " + ssl_info[1], log)
        printlog("[SSL] Bits: " + str(ssl_info[2]), log)

    # Establish identity on server
    identity = (irc_conn.config["ident"], irc_conn.config["mode"], irc_conn.config["unused"], irc_conn.config["realname"])
    irc_conn.User(identity)
    irc_conn.Nick(irc_conn.config["nick"])

    return (irc_conn, plugins)


def client_loop(irc_conn, plugins, log=None):
    if irc_conn is None:
        print "No connection established."
        sys.exit(0)

    while True:
        # Buffer to store data from server
        data = ''

        while True:
            # Receive data from connection
            tmpdata = irc_conn.sock.recv(4096)
            data = data + tmpdata

            if len(tmpdata) < 4096:
                break

        # If no incoming data exists then connection has closed
        if len(tmpdata) == 0:
            print "Connection closed."
            raw_input()
            sys.exit(0)

        # Split data to easily deal with it
        data = tmpdata.split("\r\n")

        # Parse IRC line by line
        for line in data:

            # Ignore empty lines
            if len(line) > 0:

                # Print/log line, parse it and respond
                printlog(line, log)
                irc_conn.pack = irc_conn.Parser(line)

                # Run all plugins main() function
                wait = ''
                if irc_conn.config["plugins"]:
                    for plugin in plugins:
                        wait = plugin.main.main(irc_conn)
                        if wait == "QUIT":
                            break

                # Ping Pong, keep the connection alive.
                if irc_conn.pack["cmd"] == "PING":
                    irc_conn.Pong(irc_conn.pack["text"])

                # Send user mode message after command 001
                elif irc_conn.pack["cmd"] == "001":
                    irc_conn.Mode(irc_conn.config["nick"], irc_conn.config["mode"])

                elif irc_conn.pack["cmd"] == "NOTICE":
                    if irc_conn.pack["ident"] == "NickServ":
                        # Send password after NickServ informs you
                        # that your nick is registered
                        pattern = r"[Tt]his nickname is registered"
                        if re.search(pattern, irc_conn.pack["text"]):
                            irc_conn.Identify(irc_conn.config["password"])
                            irc_conn.Join(irc_conn.config["channel"])

        if log:
            log.flush()

        # Wait for QUIT to be returned from any plugin's main() function
        if wait == "QUIT":
            # Quit, close connection and logfile.
            irc_conn.Quit("Fleabot https://github.com/Kris619/Flea")
            irc_conn.sock.close()
            if log:
                log.close()

            print "Press the [ENTER] key to close."
            raw_input()
            sys.exit(0)


def main():
    (irc_conn, plugins) = init_connection()
    client_loop(irc_conn, plugins)
