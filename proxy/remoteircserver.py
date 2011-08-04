
import time
from itertools import imap

from eventlist import EventList

SERVER_COMMANDS = [
    "action",
    "admin",
    "ctcp",
    "ctcp_reply",
    "globopts",
    "info",
    "invite",
    "ison",
    "join",
    "kick",
    "links",
    "list",
    "lusers",
    "mode",
    "motd",
    "names",
    "nick",
    "notice",
    "oper",
    "part",
    "pass",
    "ping",
    "pong",
    "privmsg",
    "privmsg_many",
    "quit",
    "squit",
    "stats",
    "time",
    "topic",
    "trace",
    "user",
    "userhost",
    "users",
    "version",
    "wallops",
    "who",
    "whois",
    "whowas",
]

class RemoteIRCServer(object):
    '''Represents an IRC Server that the client has connected to.'''

    def __init__(self, connection, server_name, nick_name, uri, port, password=None,
        ssl=False, ipv6=False):

        self.connection = connection
        self.server_name = server_name
        self.nick_name = nick_name
        self.uri = uri
        self.port = port

        self.connection.connect(uri, port, nick_name, password,
            ssl, ipv6)

        self.channels = {}
        self.events = EventList()

    def _handle_irc_event(self, event):

        # Hand event to channel, if applicable
        if event["target"] and event["target"][0] in "#&+!":
            for channel in self.channels.itervalues():
                if channel.channel_name == event["target"]:
                    channel._handle_irc_event(event)
                    return

        # Event has no channel
        self.events.append(event)
        #print "EVENT WITH NO CHANNEL:", event

    def _server_command(self, command, params):
        #print "Command:", command, params
        if command in SERVER_COMMANDS:
            func = getattr(self.connection, command)
            func(*params)

    def _dispatch_channel_method(self, method, params):

        # Method inside this instance
        func = getattr(self, "channel_%s" % method, None)
        if func != None and callable(func):
            return func(*params)

        # Method inside channel object
        # Check to make sure method is not private is done in
        # IRCProxy._dispatch, which calls this function.
        channel = self.channels[params[0]]
        func = getattr(channel, method, None)
        if func != None and callable(func):
            return func(*params[1:])

        raise ValueError('Channel method "%s" is not supported' % method)

    def channel_join(self, channel_name):
        channel = RemoteIRCChannel(self, channel_name)
        self.channels[channel_name] = channel
        return True

    def channel_list(self):
        return self.channels.keys()

    def channel_leave(self, channel_name, message=""):
        channel = self.channels[channel_name]
        channel._leave()
        del channels[channel_name]
        return True

    def disconnect(self, leave_message=""):
        for channel in self.channels:
            channel.leave(leave_message)
        self.connection.disconnect(leave_message)
        return True

    def get_channel_event_slice(self, start_index, end_index):
        channel_events = imap(lambda x: x.get_event_slice(start_index,
                              end_index), self.channels)
        return reduce(lambda x,y: x+y, channel_events)

    def get_channel_events_since(self, start_time):
        channel_events = imap(lambda x: x.get_events_since(start_index),
                              self.channels)
        return reduce(lambda x,y: x+y, channel_events)

    def get_event_slice(self, start_index, end_index):
        return self.events.get_event_slice(start_index, end_index)

    def get_events_since(self, start_time):
        return self.events.get_events_since(start_time)

class RemoteIRCChannel(object):

    def __init__(self, server, channel_name):
        self.server = server
        self.channel_name = channel_name

        self.server.connection.join(self.channel_name)
        self.events = EventList()

    def _handle_irc_event(self, event):
        #print "Event:", event #XXX
        self.events.append(event)

    def _leave(self, message):
        self.server.connection.part(channel_name, message)

    def get_event_slice(self, start_index, end_index):
        return self.events.get_event_slice(start_index, end_index)

    def get_events_since(self, start_time):
        return self.events.get_events_since(start_time)

    def message(self, message):
        self.events.append({
            "server": self.server.server_name,
            "type": "privmsg",
            "source": self.server.nick_name,
            "target": self.channel_name,
            "arguments": [message],
            "time": time.time(),
        })
        self.server.connection.privmsg(self.channel_name, message)
        return True
