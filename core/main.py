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
import socket
import ssl

def main():
    config = cfgParser("settings.conf")

    # Create socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    # Wrap socket object to create SSLSocket object
    sock = ssl.wrap_socket(sock)

    # Connect to IRC server
    sock.connect((config["host"], config["port"]))
    print "Connecting to "+config["host"]+':'+str(config["port"])

    # Display SSL information to the user
    ssl_info = sock.cipher()
    if ssl_info != None:
        print "[SSL] Cipher: "+ssl_info[0]
        print "[SSL] Version: "+ssl_info[1]
        print "[SSL] Bits: "+str(ssl_info[2])

    while True:
        # Buffer to store data from server
        data = ''

        while True:
            # Receive data from connection
            tmpdata = sock.recv(4096)
            data = data + tmpdata

            if len(tmpdata) < 4096:
                break
        
        # If no incoming data exists then connection has closed
        if len(tmpdata) == 0:
            input("Connection closed.")
            sys.exit()

        # Split data to easily deal with it
        data = tmpdata.split("\r\n")
        for line in data:
            if len(line) > 0:
                print line

main()

