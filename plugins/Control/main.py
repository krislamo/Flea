import re

# Init
controlchan = ''
chans = {}
access = []
queue = []


def chkcontrol(irc):
    global access
    global queue

    nick = irc.pack["nick"]

    for person in access:
        if nick == person:
            return True

    if queue.count(nick) == 0:
        queue.append(nick)
        irc.Whois(nick)

def noaccess(irc):
    msg = "You don't have access to that."
    irc.Notice(msg, irc.pack["nick"])

def main(irc):
    global controlchan
    global access
    global chans
    global queue

    # Set control channel
    controlchan = irc.config["channel"]

    # NOTICEs are used to "control" Flea
    if irc.pack["cmd"] == "NOTICE":

        # Nick must match the nick in settings
        # e.g. control = Kris
        if irc.pack["nick"] == irc.config["control"]:

            # Split message by spaces, for functions with
            # required parameters. e.g. "<cmd> <param1> <param2>"
            if irc.pack["text"].find(' ') != -1:
                command = irc.pack["text"].lower().split(' ')

                # Command Flea to join a channel
                if command[0] == "join":
                    if chkcontrol(irc):
                        irc.Join(command[1])
                    else:
                        noaccess(irc)

                # Command Flea to part
                elif command[0] == "part":
                    if chkcontrol(irc):
                        irc.Part(command[1],
                            "Fleabot https://github.com/Kris619/Flea")
                    else:
                        noaccess(irc)

            # Single word commands
            else:
                if irc.pack["text"] == "acc":
                    if chkcontrol(irc):
                        irc.Notice("You already have access to Control.",
                                    irc.pack["nick"])
                    else:
                        noaccess(irc)

                if irc.pack["text"] == "quit":
                    if chkcontrol(irc):
                        irc.Quit("Fleabot https://github.com/Kris619/Flea")
                        quit()
                    else:
                        noaccess(irc)

    # Check if commanding Nick is identified
    elif irc.pack["cmd"] == "307":
        if irc.pack["text"] == "is identified for this nick":

            # Check if Nick is in the queue for access list
            if queue.count(irc.pack["params"][1]) == 1:

                # Remove Nick from queue
                queue.remove(irc.pack["params"][1])

                # Check if user is set to control in settings
                # e.g. control = Kris
                if irc.pack["params"][1] == irc.config["control"]:


                    # Is control user inside the control channel?
                    if chans[controlchan].count(irc.pack["params"][1]) == 1:

                        # Grant access
                        access.append(irc.pack["params"][1])

                        print irc.pack["params"][1]+" added to Access"

                        irc.Notice(
                            "You have been given access to Control.",
                            irc.pack["params"][1])
                else:
                    irc.Notice(
                        "You are not in the Control channel: "+controlchan,
                        irc.pack["params"][1])

    # Keep track of users in every channel
    # "353" lists users to a channel
    elif irc.pack["cmd"] == "353":

        # If channel is in dictionary of channels
        if chans.keys().count(irc.pack["params"][2]) == 1:

            # Split list of channel users by space
            # "+Kris @Flea"  >  ["+Kris", "@Flea"]
            if irc.pack["text"].find(' ') != -1:
                chan_nicks = irc.pack["text"].split(' ')

                for aNick in chan_nicks:
                    if aNick != '':

                        # Remove prefix; e.g. "+Kris" > "Kris"
                        if re.search("^[~&@%+]", aNick):
                            aNick = aNick[1:]

                        # Add nick to it's channel
                        chans[irc.pack["params"][2]].append(aNick)

    # Track users joining channels
    elif irc.pack["cmd"] == "JOIN":

        # Check to see if it is the bot that joined
        if irc.pack["nick"] == irc.config["nick"]:
            # Create channel user list if it doesn't exist
            if chans.keys().count(irc.pack["text"]) == 0:
                chans[irc.pack["text"]] = []

        # Another user joined
        else:
            # Add user to channel; chans["#Channel"].append("Kris")
            chans[irc.pack["text"]].append(irc.pack["nick"])

    # Track users parting from the channel
    elif irc.pack["cmd"] == "PART":
        # Remove nick from channel they parted from
        chans[irc.pack["params"][0]].remove(irc.pack["nick"])

        # If someone parted the control channel
        # check if it was someone on the access list
        if irc.pack["params"][0] == controlchan:
            for usr in access:
                if usr == irc.pack["nick"]:
                    # Someone on the access list left.
                    access.remove(irc.pack["nick"])
                    print irc.pack["nick"]+" removed from Access"

    # Track users parting from the channel
    elif irc.pack["cmd"] == "QUIT":

        # Remove user from channels
        for channel in chans.keys():
            if chans[channel].count(irc.pack["nick"]) == 1:
                chans[channel].remove(irc.pack["nick"])

        # Remove access if user quitting had it
        for usr in access:
            if usr == irc.pack["nick"]:
                access.remove(irc.pack["nick"])
                print irc.pack["nick"]+" removed from Access"

    # Track users being kicked from the channel
    elif irc.pack["cmd"] == "KICK":

        # Remove nick from channel they were kicked from
        chans[irc.pack["params"][0]].remove(irc.pack["params"][1])

        # If someone was kicked from the control channel
        # check if it was someone on the access list
        if irc.pack["params"][0] == controlchan:
            if irc.pack["params"][1] == irc.config["nick"]:
                print "Access list is erased, control channel is gone"
                access = []
            else:
                for usr in access:
                    if usr == irc.pack["params"][1]:
                        # Someone on the access list was kicked.
                        access.remove(irc.pack["params"][1])
                        print irc.pack["params"][1]+" removed from Access"

    # Track users changing their nick
    elif irc.pack["cmd"] == "NICK":

        for channel in chans.keys():
            if channel.count(irc.pack["nick"]) == 1:
                channel.remove(irc.pack["nick"])
                channel.append(irc.pack["text"])

        # Remove access to users changing their nick
        for usr in access:
            if access.count(irc.pack["nick"]) == 1:
                access.remove(irc.pack["nick"])
                print irc.pack["nick"]+" removed from Access"
