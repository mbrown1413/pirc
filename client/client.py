
from multiprocessing import Process, Pipe
import xmlrpclib
import time
import os.path
import socket
from sys import exit

from interfaces import WXInterface
from formatter import Formatter
from common import securexmlrpc
from common import config

class IRCProxyClient(object):

    def __init__(self, conf):
        self.proxy_address = conf.proxy_address
        self.proxy_port = conf.proxy_port
        self.interface = None  # Defined later in self.run
        self.formatter = Formatter(self)

        # Makes sure files exist
        #TODO: Reference documentation on how to generate these files.
        if not os.path.exists(conf.cert_file):
            raise RuntimeError('cert_file "%s" not found!' % conf.cert_file)
        if conf.key_file and not os.path.exists(conf.key_file):
            raise RuntimeError('key_file "%s" not found!' % conf.key_file)
        if not os.path.exists(conf.accepted_certs_file):
            raise RuntimeError('accepted_certs_file "%s" not found!' % conf.accepted_certs_file)

        #TODO: proxy and port need to be parsed more robustly with urlparse
        self.proxy = xmlrpclib.ServerProxy(
            "%s:%s/" % (self.proxy_address, self.proxy_port),
            transport = securexmlrpc.HTTPSTransport(
                certfile = conf.cert_file,
                keyfile = conf.key_file,
                ca_certs = conf.accepted_certs_file,
            )
        )

        # Start event subprocess
        self.event_pipe, child_conn = Pipe()
        self.event_process = Process(target=event_loop, args=(self.proxy,
                                     child_conn,))
        self.event_process.start()

    def get_events(self):
        if self.event_pipe.poll(0.1):
            events = self.event_pipe.recv()
            if isinstance(events, _KillSignal):
                exit(1)
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
        .. todo:: Some basic event checking: ex, make sure type field is
                  present.

        '''
        event_type = event['type']

        # Notify interface, if applicable
        if event_type == "server_connect":
            self.interface.on_server_connect(event['server'])
        elif event_type == "server_disconnect":
            self.interface.on_server_disconnect(event['server'])
        elif event_type == "channel_join":
            if event['this_user']:
                self.interface.on_channel_join(event['server'], event['target'])
                return
        elif event_type == "channel_part":
            if event['this_user']:
                self.interface.on_channel_part(event['server'], event['target'])
                return

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
            The server that the command corresponds to, or None if no server is
            appropriate.

        :param channel:
            The channel that the command corresponds to, or None if no channel
            is appropriate.

        .. todo:: Reference command specification

        '''

        try:

            # Command
            if len(command_string) and command_string[0] == '/':

                terms = command_string.split(' ')
                command = terms[0][1:]
                args = terms[1:]

                if command == "connect":
                    if len(args) == 2:
                        self.proxy.server_connect(args[0], args[1], self.conf.default_username)
                    elif len(args) == 3:
                        self.proxy.server_connect(*args)
                    else:
                        #TODO: Print useage message
                        print "Wrong number of args"

                elif command == "join":
                    if len(args) != 1:
                        #TODO: Print useage message
                        print "Wrong number of args"
                    elif not server:
                        #TODO: Print useage message
                        print "You must connect a server before joining a channel"
                    else:
                        self.proxy.channel_join(server, args[0])

                elif command == "leave" or command == "part":
                    if not server or not channel:
                        if len(args) == 2:
                            self.proxy.channel_part(*args)
                        else:
                            #TODO: Print useage message
                            print "Wrong number of args"
                    else:
                        self.proxy.channel_part(server, channel)

                else:
                    print "Warning: Bad command!"
                    pass #TODO: Invalid command, provide help!

            # Privmsg
            elif server and channel:
                self.proxy.channel_message(server, channel, command_string)

            # Nothing
            else:
                #TODO: Provide better help!
                print "Cannot chat outside of a channel!"

        except xmlrpclib.Fault as fault:
            self.put_text(server, channel, "Error: %s" % fault.faultString)

    def put_text(self, server, channel, text):
        '''Pass through function for interface.put_text.

        Called by self.formatter to give text to self.interface.

        '''

        self.interface.put_text(server, channel, text)


def event_loop(proxy_server, pipe):
    last_event_time = 0
    last_error = None
    while True:
        try:

            events = proxy_server.get_events_since(last_event_time)
            if events:
                events.sort(key=lambda x:x['time'])
                pipe.send(events)
                last_event_time = events[-1]['time']
            if last_error != None:
                #TODO: Log
                print "Connection to proxy resumed!"
                last_error = None

        # Fail gracefully when proxy cannot be accessed
        except socket.gaierror as e:
            if str(e) != str(last_error):  # Ignore repeat errors
                #TODO: Log
                print "Unable to reach proxy:", e
                last_error = e

        # Kill superprocess before raising
        except Exception as e:
            pipe.send(_KillSignal())
            raise

        time.sleep(2)

class _KillSignal(Exception):
    '''Sent between processes to indicate that the recipienc should exit.'''
    pass

