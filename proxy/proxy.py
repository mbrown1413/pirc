
import time
import traceback
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Fault

#TODO: Catch an import error from this library
import irclib

from remoteircserver import RemoteIRCServer
from errors import ServerError
from eventlist import EventList

class IRCProxyServer(object):
    '''The XMLRPC interface that proxy clients use.

    An instance of this class is served via XMLRPC.  Proxy clients use it to
    get events and send events to IRC servers.  This means that any functions
    that don't start with an underscore is served directly via XMLRPC.

    When an event is received from an IRC server, _handle_irc_event is called.

    '''

    def __init__(self, bind_address, bind_port):
        '''Starts the irc client library and XMLRPC Server.'''
        self.remote_irc_servers = {}
        self.events = EventList()

        self.irc_client = irclib.IRC()
        self.irc_client.add_global_handler("all_events", self._handle_irc_event)

        # Start xmlrpc server
        self.xmlrpc_server = SimpleXMLRPCServer((bind_address, bind_port))
        self.xmlrpc_server.register_instance(self)
        self.xmlrpc_server.timeout = 0.1 # Make handle_request() non-blocking

    def _run(self):
        '''Run proxy server forever in a loop.'''
        while True:
            self._loop_iteration()

    def _loop_iteration(self):
        '''A single iteration of the _run()'s main loop.

        Handles one xmlrpc request if available and pending IRC events.

        '''
        self.xmlrpc_server.handle_request()
        self.irc_client.process_once(0.1)

    def _dispatch(self, method, params):
        '''Delegate XMLRPC requests to the appropriate method.

        The method could be in a few different places.  Here are the places
        that are checked, in order:
            # IRCProxyServer.<method>
            # If the method name starts with "server_", that prefix is taken
              off and RemoteIRCServer.<method_stripped> is searched.  The first
              argument is assumed to be the server name, and the method inside
              the appropriate server is called.
            # If the method name starts with "channel_", that prefix is taken
              off and RemoteIRCChannel.<method_stripped> is searched.  The
              first two arguments are assumed to be server name and channel
              name, and server._dispatch_channel_method is called for the
              appropriate server.

        :param method:
            Name of the XMLRPC method requested.

        :param params:
            A tuple of the parameters given in the XMLRPC call.

        :returns:
            The return value of the method that was called.  An XMLRPC Fault is
            returned for any errors.

        '''

        try:

            # Method inside IRCProxyServer (this instance)
            func = getattr(self, method, None)
            if func != None and callable(func):
                return func(*params)

            # Method inside a RemoteIRCServer instance
            elif method.startswith("server_") and len(params) > 0:
                server = self.remote_irc_servers[params[0]]
                method_name = method.lstrip("server_")
                if not method_name.startswith("_"):
                    func = getattr(server, method_name)
                    if callable(func):
                        return func(*params[1:])

            # Method inside a RemoteIRCChannel instance
            # Pass this to a RemoteIRCServer, which will pass it to a
            # RemoteIRCChannel instance.
            elif method.startswith("channel_") and len(params) > 0:
                server = self.remote_irc_servers[params[0]]
                method_name = method.lstrip("channel_")
                if not method_name.startswith("_"):
                    return server._dispatch_channel_method(method_name, params[1:])

            # Method not found!
            #TODO: Log
            raise ServerError('Proxy server does not support method "%s".' % method)

        except ServerError as e:
            #TODO: Log
            return Fault(2, ' '.join(e.args))

        except Exception as e:
            #TODO: Log
            traceback.print_exc()
            return Fault(3, "Proxy server received an unexpected error.  See log file for details.")

    def _handle_irc_event(self, connection, irc_event):
        '''Callback for any events from irclib.

        Converts the irc_event object into a dictionary, then gives the
        dictionary to the server it belongs to.

        :param connection:
            Connection that caused this event.  See irclib for details.

        :param irc_event:
            A small storage object for the incoming event provided by irclib.

        '''

        try:

            # Ignore raw messages and pings
            if irc_event._eventtype == "all_raw_messages" or \
                irc_event._eventtype == "ping":

                return

            event = {

                # Attributes from IRC
                "type": irc_event._eventtype,
                "source": irc_event._source,
                "target": irc_event._target,
                "arguments": irc_event._arguments,

                # Extra attributes
                "server": False,
                "channel": False,
                "time": time.time(),

            }

            # Give this event to its respective server object
            for server in self.remote_irc_servers.itervalues():
                if server.connection == connection:
                    event["server"] = server.server_name
                    server._handle_irc_event(event)
                    return

            #TODO: Log
            print "EVENT WITHOUT SERVER:", event

        except ServerError as e:
            #TODO: Log
            traceback.print_exc()

        except Exception as e:
            #TODO: Log
            traceback.print_exc()

    def get_events_since(self, start_time):
        events = self.events.get_events_since(start_time)
        for server in self.remote_irc_servers.itervalues():
            events.extend(server._get_events_since(start_time))
        return events

    def server_list(self):
        '''List server names that are connected.

        :returns:
            A list of server names.

        '''
        return self.remote_irc_servers.keys()

    def server_connect(self, server_name, nick_name, uri, port=6667,
                       password=None, ssl=False, ipv6=False):
        '''Connect to a server.

        :param server_name:
            A short identifying name for this server.  This name will be used
            to reference the server in the future.

        :param nick_name:
            The name to use to connect to the server.

        :param uri:
            URI of the server.

        :param port:
            Port number of the server.  Default 6667.

        :param password:
            Password, if any, to present to the server.

        :param ssl:
            If True, ssl is used to connect to the server.

        :param ipv6:
            If True, ipv6 is used to connect to the server.

        '''
        connection = self.irc_client.server()
        remote_server = RemoteIRCServer(connection, server_name, nick_name,
                                        uri, port, password, ssl, ipv6)
        self.remote_irc_servers[server_name] = remote_server
        self.events.append(type="server_join", server=server_name)
        return True

    def server_disconnect(self, server_name, leave_message=""):
        '''Disconnect from the remote IRC server.

        :param server_name:
            The name of the server that was given in server_connect().

        :param leave_message:
            A message that is given to each channel and the server when
            leaving.

        '''
        server = self.remote_irc_servers[server_name]
        server._disconnect(leave_message)
        del self.remote_irc_servers[server_name]
        self.events.append(type="server_disconnect", server=server_name)
        return True

def run(bind_port=2939, bind_address="0.0.0.0"):
    '''Runs the proxy server.'''

    # Start local IRC client and proxy
    proxy = IRCProxyServer(bind_address, bind_port)
    proxy._run()

if __name__ == "__main__":
    run()

