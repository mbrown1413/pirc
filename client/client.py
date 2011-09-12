
from multiprocessing import Process, Pipe
import xmlrpclib
import time

from interfaces import WXInterface
from printevent import print_event

class IRCProxyClient(object):

    def __init__(self, proxy_address, proxy_port=2939):
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.interface = None

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
        if event['type'] == "channel_join":
            print "CHANNEL_JOIN:", event
            self.interface.on_channel_join(event['server'], event['channel'])

        print_event(event, self.interface)

    def run_command(self, command_string, server=None, channel=None):
        print command_string  #XXX

        # Command
        if len(command_string) and command_string[0] == '/':

            terms = command_string.split(' ')
            command = terms[0][1:]
            args = terms[1:]

            if command == "connect":
                self.proxy.server_connect(*args)
            elif command == "join":
                self.proxy.channel_join(*args)

        # Privmsg
        elif server and channel:
            self.proxy.channel_message(server, channel, command_string)

        # Nothing
        else:
            pass


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

