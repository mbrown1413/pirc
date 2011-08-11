
from multiprocessing import Process, Pipe
import xmlrpclib
import time

from interfaces import WXInterface

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
        self.event_process = Process(target=event_loop, args=(self.proxy, child_conn,))
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
            self.interface.uninitialize()

    def handle_events(self):
        events = self.get_events()
        for event in events:
            self.handle_event(event)

    def handle_event(self, event):
        print event  #XXX
        self.interface.put_text(str(event))
        self.interface.put_text("\n")
        # TODO: Call Event Handler

    def run_command(self, command, server=None, channel=None):
        print command  #XXX
        #TODO: Call Command Parser


def event_loop(proxy_server, pipe):
    last_event_time = 0
    while True:
        events = proxy_server.get_events_since(last_event_time)
        if events:
            #TODO: Sort events by timestamp
            pipe.send(events)
            last_event_time = time.time()
        time.sleep(1)

if __name__ == "__main__":
    client = IRCProxyClient("http://localhost")
    interface = WXInterface(client)
    client.run(interface)

