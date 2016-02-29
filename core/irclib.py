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

# Built-in to Python 2.7
import socket
import re

class irc:

    debug = False
    log = False
    config = {}
    pack = {}
    sock = socket.socket()

    # IRC Parser. Parses by line
    def Parser(self, line):
        packet = {"nick":None, "ident":None,
              "host":None, "cmd":None,
              "params":[], "text":None}

        if len(line) > 0:
            if(line[0] == ':'):
                part, line = line.split(' ', 1)

                ATL = part.find('@')
                EXL = part.find('!')

                # Nick
                if EXL > -1:
                    packet["nick"] = part[1:EXL]
                elif ATL > -1:
                    packet["nick"] = part[1:ATL+1]
                else:
                    packet["nick"] = part[1:]

                # Ident
                if ATL > -1 and EXL > -1:
                    packet["ident"] = part[EXL+1:ATL]
                # Host
                if ATL > -1:
                    packet["host"] = part[ATL+1:]

            part, line = line.split(' ', 1)

            # Command & Params
            params = []
            packet["cmd"] = part

            while True:
                if line.find(' ') > -1:
                    part, line = line.split(' ', 1)

                    if part[0] != ':':
                        packet["params"].append(part)
                    else:
                        packet["text"] = part[1:]+" "+line
                        break
                elif len(line) > 1:
                    if line[0] == ':':
                        packet["text"] = line[1:]
                    else:
                        packet["params"].append(line)
                    break
                else:
                    break

            return packet


    # Basic message function to send and log any data
    def msg(self, message):
        self.sock.send(message+"\r\n")

        # Match messages containing private information
        # then censors it to output to the terminal and log
        pattern = r"^PRIVMSG NickServ :IDENTIFY *"
        if re.search(pattern, message):
            message = "PRIVMSG NickServ :IDENTIFY ****"

        output = ">>> "+message

        if self.debug:
            print output
        if self.log:
            self.log.write(output+"\n")

    def User(self, nick, mode, unused, owner):
        self.msg("USER "+nick+' '+mode+' '+unused+" :"+owner)

    def Nick(self, nick):
        self.msg("NICK "+nick)

    def Pong(self, txt):
        self.msg("PONG :"+txt)

    def Mode(self, nick, mode):
        self.msg("MODE "+ nick + " "+mode)

    def PrivMsg(self, user, message):
        self.msg("PRIVMSG "+user+" :"+message)

    def Identify(self, password):
        self.PrivMsg("NickServ", "IDENTIFY "+password)

    def Join(self, channel):
        self.msg("JOIN "+channel)

    def Quit(self, quitmsg):
        self.msg("QUIT :"+quitmsg)

    def Notice(self, message, user):
        self.msg("NOTICE "+user+" :"+message)

    def Part(self, channel, message):
        self.msg("PART "+channel+" "+message)

    def ReturnVersion(self, version, user):
        self.msg("NOTICE "+user+" :\001VERSION "+version+"\001")

    def Whois(self, query):
        self.msg("WHOIS "+query)

    def SetMode(self, channel, nick, mode):
        self.msg("MODE "+channel+" "+mode+" "+nick)

