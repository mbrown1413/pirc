
import xmlrpclib

class IRCClient(object):

    def __init__(self, interface, proxy_address, proxy_port=2939):

        self.interface = interface
        self.proxy_address = proxy_address
        self.proxy_port = 2939

        #TODO: proxy and port need to be parsed more robustly with urlparse
        self.proxy = xmlrpclib.ServerProxy(
            "%s:%s/" % (proxy_address, proxy_port))

        # Servers that we will request events from
        self.active_servers = [] # Empty means all servers are interesting

    def run(self):

        #TODO: Timeout should be some kind of an exponential
        # falloff since the last event
        timeout = 1000 

        try:
            self.interface.init(self)
            last_event_time = 0 # TODO
            while True:
                events = self.proxy.get_events_since(last_event_time)
                for event in events:
                    self.interface.on_event(event)
                    if last_event_time < event['time']:
                        last_event_time = event['time']

                command = self.interface.get_command(timeout)
                if command:
                    self.do_command(command)

        finally:
            self.interface.uninitialize()

    def do_command(self, server_name, channel, command):
        #TODO: Actually parse for commands
        self.proxy.privmsg(server_name, channel, command)

    def set_active_servers(self, servers):
        self.active_servers = servers
