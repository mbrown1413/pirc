
import time
import traceback
import os.path
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Fault

#TODO: Catch an import error from this library
import irclib

from remoteircserver import RemoteIRCServer
from errors import ServerError
from eventlist import EventList
from ircevents import format_irc_event
from tools import type_check
from common import securexmlrpc

class IRCProxyServer(object):
    '''The XMLRPC interface that proxy clients use.

    An instance of this class is served via XMLRPC.  Proxy clients use it to
    get events and send events to IRC servers.  This means that any functions
    that don't start with an underscore is served directly via XMLRPC.

    When an event is received from an IRC server, _handle_irc_event is called.

    '''

    def __init__(self, conf):
        '''Starts the irc client library and XMLRPC Server.'''
        self.remote_irc_servers = {}
        self.events = EventList()

        # Makes sure files exist
        #TODO: Reference documentation on how to generate these files.
        if not os.path.exists(conf.cert_file):
            raise RuntimeError('cert_file "%s" not found!' % conf.cert_file)
        if conf.key_file and not os.path.exists(conf.key_file):
            raise RuntimeError('key_file "%s" not found!' % conf.key_file)
        if not os.path.exists(conf.accepted_certs_file):
            raise RuntimeError('accepted_certs_file "%s" not found!' % conf.accepted_certs_file)

        self.irc_client = irclib.IRC()
        self.irc_client.add_global_handler("all_events", self._handle_irc_event)

        # Start xmlrpc server
        self.xmlrpc_server = securexmlrpc.SecureXMLRPCServer(
            (conf.bind_address, conf.bind_port),
            certfile = conf.cert_file,
            keyfile = conf.key_file,
            ca_certs = conf.accepted_certs_file,
        )
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
        #TODO: Double check typechecking in all _dispatch methods.

        try:

            # Method inside IRCProxyServer (this instance)
            func = getattr(self, method, None)
            if func != None and callable(func):
                return func(*params)

            # Look for method inside a RemoteIRCServer instance
            # Prefix of server_
            elif method.startswith("server_"):
                return self._dispatch_server(method, params)

            # Look for method inside a RemoteIRCChannel instance
            # Prefix of channel_
            elif method.startswith("channel_") and len(params) > 0:
                return self._dispatch_channel(method, params)

            # Method not found!
            raise ServerError('Method "%s" not found.' % method)

        except ServerError as e:
            #TODO: Log
            raise Fault(2, ' '.join(e.args))

        except Exception as e:
            #TODO: Log
            traceback.print_exc()
            raise Fault(3, "Proxy server received an unexpected error.  See log file for details.")

    def _dispatch_server(self, method, params):
        '''Dispatch for xmlrpc methods starting with _server.'''

        # Check for method existence and callability
        server_method = method[len("server_"):]
        if not server_method.startswith("_") and \
                callable(getattr(RemoteIRCServer, server_method, None)):

            # Get server
            if len(params) <= 0:
                raise ServerError('Not enough arguments for method "%s".' % method)
            server_name = params[0]
            type_check("server_name", server_name, basestring)
            if server_name not in self.remote_irc_servers:
                raise ServerError('Server with name "%s" was not found' % server_name)
            server = self.remote_irc_servers[server_name]

            # Call server method
            func = getattr(server, server_method)
            return func(*params[1:])

        raise ServerError('Method "%s" not found.' % method)

    def _dispatch_channel(self, method, params):
        '''Dispatch for xmlrpc methods starting with _channel.'''

        # Checks for methods existance an non-privacy are done in
        # RemoteIRCServer._dispatch_channel_method

        # Get server
        if len(params) <= 0:
            raise ServerError('Not enough arguments for method "%s".' % method)
        server_name = params[0]
        type_check("server_name", server_name, basestring)
        if server_name not in self.remote_irc_servers:
            raise ServerError('Server with name "%s" was not found' % server_name)
        server = self.remote_irc_servers[server_name]

        # Dispatch to corresponding server
        return server._dispatch_channel_method(method, params[1:])

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

            irc_event.connection = connection
            event = format_irc_event(irc_event, self)
            if not event: return
            server = self.remote_irc_servers[event['server']]
            server._handle_irc_event(event)

        except ServerError as e:
            #TODO: Log
            traceback.print_exc()

        except Exception as e:
            #TODO: Log
            traceback.print_exc()

    def get_events_since(self, start_time):
        type_check("start_time", start_time, int, float)
        if start_time < 0:
            raise ServerError("start_time must be a positive number.")

        events = self.events.get_events_since(start_time)
        for server in self.remote_irc_servers.itervalues():
            events.extend(server._get_events_since(start_time))
        return events

    def server_list(self):
        return self.remote_irc_servers.keys()

    def server_connect(self, server_name, nick_name, uri, port=6667,
                       password="", ssl=False, ipv6=False):
        type_check("server_name", server_name, basestring)
        type_check("nick_name", nick_name, basestring)
        type_check("uri", uri, basestring)
        type_check("port", port, int)
        type_check("password", password, basestring)
        type_check("ssl", ssl, bool)
        type_check("ipv6", ipv6, bool)

        if not password:
            password = None
        if server_name in self.server_list():
            raise ServerError("Server with that name is already connected!")

        connection = self.irc_client.server()
        remote_server = RemoteIRCServer(connection, server_name, nick_name,
                                        uri, port, password, ssl, ipv6)
        self.remote_irc_servers[server_name] = remote_server
        self.events.append(type="server_connect", server=server_name)
        return True

    def server_disconnect(self, server_name, leave_message=""):
        type_check("server_name", server_name, basestring)
        type_check("leave_message", leave_message, basestring)
        if server_name not in self.remote_irc_servers:
            raise ServerError('Server with name="%s" does not exist' % server_name)

        server = self.remote_irc_servers[server_name]
        server._disconnect(leave_message)
        del self.remote_irc_servers[server_name]
        self.events.append(type="server_disconnect", server=server_name)
        return True

