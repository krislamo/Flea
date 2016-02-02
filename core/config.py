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

import re

def cfgParser(cfgFile):

    # Dictionary to hold final data
    # e.g. settings["nick"] = "Flea"
    settings = {}

    # Open configuration file and read file by lines
    cfgFile = open(cfgFile)
    cfgLines = cfgFile.readlines()

    # Loop through every line
    # e.g. "nick = Flea \n"
    for line in cfgLines:

        # Keep track of whether or not it is a variable or value
        # 0. Variable
        # 1. Value
        counter = 0

        # Find if an equals sign (=) exists, if so split there
        # otherwise skip to the next line.
        if line.find('='):
            pieces = line.split('=')

            # Check for 2 parts to the list, both a variable and value
            # e.g. ["nick ", " Flea \n"]
            if len(pieces) == 2:

                # Check out an individual part
                # e.g. "nick " or " Flea \n"
                for part in pieces:

                    # Remove newline character if it exists
                    if part[-1] == '\n':
                        part = part[:-1]

                    # Starting points for removing spaces to individual
                    # parts; points[0] is the beginning of the string
                    # while points[1] is the end.
                    points = [0,len(part)-1]

                    # Remove whitespace trailing at the beginning
                    while True:
                        if points[0] <= len(part)-1:
                            if part[points[0]] == ' ':

                                # Remove the first character
                                part = part[points[0]+1:]
                                # Calculate end of str for length change
                                points[1] -= 1

                            else:
                                break
                        else:
                            break


                    # Remove whitespace trailing at the ending
                    while True:
                        if points[1] <= len(part)-1:
                            if part[points[1]] == ' ':

                                # Remove the last character
                                part = part[:points[1]]
                                points[1] -= 1

                            else:
                                break
                        else:
                            break

                    # Calculate where this part goes in settings
                    if counter == 0:
                        counter += 1
                        settings[part] = None

                        # Set pieces[0] to the modified variable name
                        pieces[0] = part

                    elif counter == 1:
                        counter -= 1
                        settings[pieces[0]] = part

    # Convert text to appropriate types in the settings[] dictionary
    # e.g. "6667" to int("6667"); "true" to bool("true"), etc.
    for x in settings:

        # Conversion for booleans
        if settings[x].lower() == "true":
            settings[x] = True
        elif settings[x].lower() == "false":
            settings[x] = False

        # Conversion for positive integers
        elif re.search("^[0-9]+$", settings[x]) != None:
            settings[x] = int(settings[x])

    return settings

