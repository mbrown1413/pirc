
from Queue import Queue
from time import time

#TODO: Catch an import error from this library
import irclib

from server import IRCServer, SERVER_COMMANDS
from common import XMLRPCServer

class IRCProxy(object):
    def __init__(self, bind_address="localhost", bind_port=2939):

        self.event_queue = Queue()

        # Init IRC client
        self.irc = irclib.IRC()
        self.servers = {}
        self.irc.add_global_handler("all_events",
            self.irc_event_dispatcher, -10)

        self.xmlrpc = self.init_xmlrpc(bind_address, bind_port)

    def get_server(self, server_name):
        return self.servers[server_name]

    def irc_event_dispatcher(self, connection, event):
        if event._eventtype == "all_raw_messages":
            # Ignore these.  We will deal with the non-raw messages
            return
        for server in self.servers.values():
            if server.connection == connection:
                server.event_dispatcher(event)
                break
        self.event_queue.put(event)

    def run(self):
        '''Main loop that handles the XMLRPC Server and the irc listener.'''
        while True:
            self.irc.process_once(0.1)
            self.xmlrpc.handle_request()

    def init_xmlrpc(self, bind_address, bind_port):
        '''Initialize the xmlrpc server and return it.'''
        server = XMLRPCServer(self.dispatch, (bind_address, bind_port))
        server.timeout = 0.1 # Make self.xmlrpc.handle_request() non-blocking

        return server

    def dispatch(self, method, params):
        '''Called by the xmlrpc server when a call comes in.

        Arguments:
        method - The name of the method called.
        params - A tuple containing the method's arguments.

        '''

        # Methods that aren't handled by IRCServer objects
        EVENT_METHODS = {
            "connect": self.connect,
            "disconnect": self.disconnect,
            "get_event_slice": self.get_event_slice,
            "get_events_since": self.get_events_since,
            "get_server_names": self.get_server_names,
        }

        if method in EVENT_METHODS:
            return EVENT_METHODS[method](*params)
        elif method in SERVER_COMMANDS:
            server = self.get_server(params[0])
            server_name = params[0]
            server = self.get_server(server_name)
            server.server_command(method, params[1:])
            return True
        else:
            #TODO: Better error
            print "INVALID METHOD!!!!!!!!!!!!!!", method

    ################# XMLRPC Server Functions ################# 
    # All of the following can be called via xmlrpc.  For a complete list of
    # xmlrpc calls, see the dispatch method.

    def connect(self, uri, port, nickname, password=None, ssl=False,
        ipv6=False):

        #TODO: Error check this connection
        server = IRCServer(self, uri, uri, port, nickname, password=None,
            ssl=False, ipv6=False)

        self.servers[uri] = server
        return True

    def disconnect(self, server_name, leave_message=None):
        pass #TODO

    def get_event_slice(self, server_name, begin, end):
        '''Get a slice of events from the server's event list.

        begin and end are indexes into the event list, with index 0 being the
        latest event.

        Example: This will get the latest 10 events:
        >>> self.get_event_slice("irc.example.com", 0, 10)

        '''

        server = self.get_server(server_name)
        return server.events[::-1][begin, end][::-1]

    def get_events_since(self, start_time, servers=None):
        '''Get events since the given time.

        start_time is a time in seconds since epoch.  If servers is given, it
        should be a list of server names to get events from.  If servers is
        None (default) all servers are looked at.

        Clients should be aware that the server time and client time may be
        slightly different, so the client should not pass values derived from
        time.time() in here.  Instead, the client should use the timestamps of
        past events received.

        '''
        if not servers:
            servers = self.servers

        events = []
        for server_name in servers:
            server = self.get_server(server_name)

            # Go through events in reverse order, until it's timestamp is
            # earlier than the given time
            for event in server.events[::-1]:
                if event['time'] <= start_time: break
                events.append(event)

        return events

    def get_server_names(self):
        '''Returns a list of the server names.'''
        return map(lambda server: server.name, servers)
