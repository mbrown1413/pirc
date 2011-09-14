
from multiprocessing import Process, Pipe
import xmlrpclib
import time

from interfaces import WXInterface
from formatter import Formatter

class IRCProxyClient(object):

    def __init__(self, proxy_address, proxy_port=2939):
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.interface = None
        self.formatter = Formatter(self)

        #TODO: proxy and port need to be parsed more robustly with urlparse
        self.proxy = xmlrpclib.ServerProxy(
            "%s:%s/" % (proxy_address, proxy_port))

        # Start event subprocess
        self.event_pipe, child_conn = Pipe()
        self.event_process = Process(target=event_loop, args=(self.proxy,
                                     child_conn,))
        self.event_process.start()

    def get_events(self):
        if self.event_pipe.poll(0.1):
            events = self.event_pipe.recv()
            return events
        else:
            return []

    def run(self, interface):
        self.interface = interface
        try:
            self.interface.initialize()
            self.interface.run()
        finally:
            self.exit()

    def exit(self):
        self.interface.uninitialize()
        self.event_process.terminate()

    def handle_events(self):
        events = self.get_events()
        for event in events:
            self.handle_event(event)

    def handle_event(self, event):
        '''Called when an event comes in.

        Responsible for:

        * Calling self.interface if necessary.  For example, on an incoming
          channel_join event, the interface must be notified so it can create a
          new window or tab.
        * Give self.formatter.print_event() the event which will then give the
          interface text to display.

        This method is called in the order that the events happen.  Event
        sorting is handled elsewhere.

        :param event:
            The event dictionary.  See the server spec for details on the event
            format.

        .. todo:: Reference event specification for event parameter.
        .. todo:: Some basic event checking: ex, make sure type field is present.

        '''

        if event['type'] == "channel_join":
            self.interface.on_channel_join(event['server'], event['channel'])
        elif event['type'] == "channel_leave":
            self.interface.on_channel_leave(event['server'], event['channel'])

        self.formatter.print_event(event)

    def run_command(self, command_string, server=None, channel=None):
        '''Called by self.interface when the user inputs text.

        Messages prefixed with '/' are interpreted as functional commands.
        Otherwise, the command is interpreted as a chat message.

        The server and channel arguments are meaningful in commands such as
        chat messages, where the user does not specify a server and channel,
        but the command still must be routed correctly.  Giving a server and
        channel when it is not needed will never cause problems.  The interface
        should always specify a server and channel if one is available.

        :param command_string:
            The raw string of text that was inputted by the user.  May or may
            not start with '/'.

        :param server:
            The server that the command corresponds to.

        :param channel:
            The channel that the command corresponds to.

        .. todo:: Reference command specification

        '''

        # Command
        if len(command_string) and command_string[0] == '/':

            terms = command_string.split(' ')
            command = terms[0][1:]
            args = terms[1:]

            if command == "connect":
                self.proxy.server_connect(*args)
            elif command == "join":
                self.proxy.channel_join(*args)
            else:
                pass #TODO: Invalid command, provide help!

        # Privmsg
        elif server and channel:
            self.proxy.channel_message(server, channel, command_string)

        # Nothing
        else:
            #TODO: Invalid command, provide help!
            print "Warning: Bad command!"

    def put_text(self, server, channel, text):
        '''Pass through function for interface.put_text.

        Called by self.formatter to give text to self.interface.

        '''

        self.interface.put_text(server, channel, text)


def event_loop(proxy_server, pipe):
    last_event_time = 0
    while True:
        events = proxy_server.get_events_since(last_event_time)
        if events:
            events.sort(key=lambda x:x['time'])
            pipe.send(events)
            last_event_time = time.time()
        time.sleep(2)

if __name__ == "__main__":
    client = IRCProxyClient("http://localhost")
    interface = WXInterface(client)
    client.run(interface)

