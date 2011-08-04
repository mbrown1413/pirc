
import time
import traceback
from SimpleXMLRPCServer import SimpleXMLRPCServer

#TODO: Catch an import error from this library
import irclib

from remoteircserver import RemoteIRCServer

class IRCProxyServer(object):
    '''The XMLRPC interface that proxy clients use.

    An instance of this class is served via XMLRPC.  Proxy clients use it to
    get events and send events to IRC servers.  This means that any functions
    that don't start with an underscore are served directly via XMLRPC.

    When an event is recieved from an IRC server, _handle_irc_event is called.

    '''

    def __init__(self, bind_address, bind_port):
        self.remote_irc_servers = {}

        self.irc_client = irclib.IRC()
        self.irc_client.add_global_handler("all_events", self._handle_irc_event)

        # Start xmlrpc server
        self.xmlrpc_server = SimpleXMLRPCServer((bind_address, bind_port))
        self.xmlrpc_server.register_instance(self)
        self.xmlrpc_server.timeout = 0.1 # Make handle_request() non-blocking

    def _run(self):
        while True:
            self.xmlrpc_server.handle_request()
            self.irc_client.process_once(0.1)

    def _dispatch(self, method, params):
        '''XMLRPC dispatch method that logs exceptions.'''

        try:

            # Method inside IRCProxyServer(this instance)
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
            msg = 'Method "%s" is not supported' % method
            #TODO: Log
            print msg
            raise ValueError(msg)

        except Exception as e:
            #TODO: Log
            traceback.print_exc()
            raise

    def _handle_irc_event(self, connection, irc_event):

        try:

            # Ignore raw messages and pings
            if irc_event._eventtype == "all_raw_messages" or \
                irc_event._eventtype == "ping":

                return

            event = {
                "server": None,
                "type": irc_event._eventtype,
                "source": irc_event._source,
                "target": irc_event._target,
                "arguments": irc_event._arguments,
                "time": time.time()
            }
            if event['source'] is None:
                event['source'] = False

            # Give this event to its respective server object
            for server in self.remote_irc_servers.itervalues():
                if server.connection == connection:
                    event["server"] = server.server_name
                    server._handle_irc_event(event)
                    return

            print "EVENT WITHOUT SERVER:", event

        except Exception as e:
            #TODO: Log
            traceback.print_exc()

    def server_list(self):
        return self.remote_irc_servers.keys()

    def server_connect(self, server_name, nick_name, uri, port=6667):
        '''Connect with the server with the given server name.'''
        #XXX
        connection = self.irc_client.server()
        remote_server = RemoteIRCServer(connection, server_name, nick_name, uri, port)
        self.remote_irc_servers[server_name] = remote_server
        return True

    def server_disconnect(self, server_name, leave_message=""):
        server = self.remote_irc_servers[server_name]
        server.disconnect(leave_message)
        del self.remote_irc_servers[server_name]
        return True

def run(bind_port=2939, bind_address="0.0.0.0"):

    # Start local IRC client and proxy
    proxy = IRCProxyServer(bind_address, bind_port)
    proxy._run()

if __name__ == "__main__":
    run()

