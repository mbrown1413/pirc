
import types
import time

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

class IRCServer(object):
    '''Represents an IRC Server.'''

    def __init__(self, irc_proxy, name, server, port, nickname, password=None,
        ssl=False, ipv6=False):

        self.name = name
        self.uri = server
        self.port = port
        self.nickname = nickname
        self.connection = irc_proxy.irc.server()
        self.connection.connect(server, port, nickname, password,
            ssl, ipv6)

        self.events = []

    def event_dispatcher(self, irc_event):
        '''Called whenever the irc server sends any event.

        The irc_event given is the raw irclib.Event object.  This function
        converts that event into an event dictionary that is stored in
        self.events.

        '''
        print "%s, %s, %s, %s" % (irc_event._eventtype, irc_event._source, irc_event._target, irc_event._arguments)
        event = {
            "server": self.name,
            "type": irc_event._eventtype,
            "source": irc_event._source,
            "target": irc_event._target,
            "arguments": irc_event._arguments,
            "time": time.time()
        }
        if event['source'] is None:
            event['source'] = False
        self.events.append(event)

    def server_command(self, command, params):
        if command == "privmsg":
            if not params[1]: return
            self.events.append({
                "server": self.name,
                "type": "privmsg",
                "source": self.nickname,
                "target": params[0],
                "arguments": [params[1]],
                "time": time.time(),
            })
        if command in SERVER_COMMANDS:
            func = getattr(self.connection, command)
            func(*params)

    def disconnect(self):
        pass #TODO
