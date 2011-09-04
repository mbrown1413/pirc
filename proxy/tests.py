
import unittest
from multiprocessing import Process
import time
import xmlrpclib

import proxy

PROXY_BIND_ADDRESS = "127.0.0.1"
PROXY_PORT = 2500

IRC_SERVER_ADDRESS = "localhost"
IRC_SERVER_PORT = 6667

def start_proxy_process(bind_address=PROXY_BIND_ADDRESS, bind_port=PROXY_PORT):
    """Starts a proxy it a separate process using python multiprocessing.

    Returns the multiprocessing.Process object, which can be killed by calling
    its .terminate() method.

    """
    p = Process(target=proxy.run, args=(bind_port, bind_address))
    p.start()

    # Make sure process has started
    while not p.is_alive() or p.pid == None:
        time.sleep(0.1)
        if p.exitcode != None:
            raise RuntimeError("Proxy process could not be started!")

    # Give process enough time to start listening on the socket.
    # Of course, this is a horrible way of solving a race condition.
    #TODO: Race condition!
    time.sleep(0.1)

    return p

def get_xmlrpc_client(address="http://127.0.0.1", port=PROXY_PORT):
    #TODO: proxy and port need to be parsed more robustly with urlparse
    return xmlrpclib.ServerProxy(
        "%s:%s/" % (address, port))

class ProxyXMLRPCTestCase(unittest.TestCase):
    """Tests connecting and disconnecting to IRC servers."""

    def setUp(self):
        self.proxy = get_xmlrpc_client()

        servers = self.proxy.server_list()
        self.assertEquals(servers, [], "Server list was not empty at the start"
            " of the test.  This is a previous test's fault.")

    def tearDown(self):

        servers = self.proxy.server_list()
        if servers != []:
            exception_message = ""
            try:
                for server_name in self.proxy.server_list():
                    self.proxy.server_disconnect(server_name)
            except Exception as e:
                exception_message = "\nThere was also an exception raised " \
                        "while trying to disconnect from the lingering " \
                        "servers: %s" % e
            self.fail("There were active servers at the end of this test.  "
                    "Tests should completely disconnect from all servers before "
                    "returning.  Server list: "+str(servers)+str(exception_message))

    ###################### Event Assertions ######################

    def get_matching_events(self, given_event, limit=0, since=0):

        matching_events = []

        events = self.proxy.get_events_since(since)
        for event in events[::-1]:

            # Does event match given_event?
            event_matches = True
            for key, value in given_event.iteritems():
                if key not in event or event[key] != value:
                    event_matches = False
                    break

            if event_matches:
                matching_events.append(event)
                if len(matching_events) == limit:
                    break

        return matching_events

    def assertMatchingEvent(self, event, since=0):
        if not self.get_matching_events(event, limit=1, since=since):
            self.fail("No event matching: %s" % event)

    def assertNoMatchingEvent(self, event, since=0):
        if self.get_matching_events(event, limit=1, since=since):
            self.fail("Matching event was found: %s" % event)

    def assertEventCount(self, event, count, since=0):
        matching_events = self.get_matching_events(event, since=since)
        if len(matching_events) != count:
            self.fail("Event count was not correct:\n"
                "Expected %s, got %s\n"
                "Given event: %s\n"
                "Matching events: %s" %
                (count, len(matching_events), event, matching_events))

    ###################### Connect/Disconnect Assertions ######################

    def assertConnectWorks(self, server_name, nick_name, uri=IRC_SERVER_ADDRESS,
                            port=IRC_SERVER_PORT):

        t = time.time()
        self.proxy.server_connect(server_name, nick_name, uri, port)
        servers = self.proxy.server_list()
        self.assertTrue(server_name in servers)
        self.assertMatchingEvent({
            'type': 'server_connect',
            'server': server_name,
        }, since=t)

    def assertConnectFails(self, server_name, nick_name, uri=IRC_SERVER_ADDRESS,
                            port=IRC_SERVER_PORT):

        servers = self.proxy.server_list()
        if server_name in servers:
            inspect_server_list = False
        else:
            inspect_server_list = True

        t = time.time()
        self.assertRaises(xmlrpclib.Fault, self.proxy.server_connect,
            server_name, nick_name, uri, port)
        if inspect_server_list:
            servers = self.proxy.server_list()
            self.assertFalse(server_name in servers)
        self.assertNoMatchingEvent({
            'type': 'server_connect',
            'server': server_name,
        }, since=t)

    def assertDisconnectWorks(self, server_name, leave_message=""):

        t = time.time()
        self.proxy.server_disconnect(server_name, leave_message)
        servers = self.proxy.server_list()
        self.assertFalse(server_name in servers)
        self.assertMatchingEvent({
            'type': 'server_disconnect',
            'server': server_name,
        }, since=t)

    def assertDisconnectFails(self, server_name, leave_message=""):

        servers = self.proxy.server_list()
        if server_name in servers:
            inspect_server_list = True
        else:
            inspect_server_list = False

        t = time.time()
        self.assertRaises(xmlrpclib.Fault, self.proxy.server_disconnect,
                          server_name)
        if inspect_server_list:
            servers = self.proxy.server_list()
            self.assertTrue(server_name in servers)
        self.assertNoMatchingEvent({
            'type': 'server_disconnect',
            'server': server_name,
        }, since=t)

    ###################### Channel Join/Leave Assertions ######################

    def assertJoinWorks(self, server_name, channel_name):

        t = time.time()
        self.proxy.channel_join(server_name, channel_name)
        channels = self.proxy.channel_list(server_name)
        self.assertTrue(channel_name in channels)
        self.assertMatchingEvent({
            'type': 'channel_join',
            'server': server_name,
            'channel': channel_name,
        }, since=t)

    def assertJoinFails(self, server_name, channel_name):

        try:
            channels = self.proxy.channel_list(server_name)
            if channel_name in channels:
                inspect_channel_list = False
            else:
                inspect_channel_list = False
        except xmlrpclib.Fault:
            # The server_name must not be connected, because channel_list
            # raised a Fault.  Don't inspect channel list because the server
            # still won't exist.
            inspect_channel_list = False

        t = time.time()
        self.assertRaises(xmlrpclib.Fault, self.proxy.channel_join,
                          server_name, channel_name)
        if inspect_channel_list:
            channels = self.proxy.channel_list(server_name)
            self.assertTrue(channel_name in channels)
        self.assertNoMatchingEvent({
            'type': 'channel_join',
            'server': server_name,
            'channel': channel_name,
        }, since=t)

    def assertLeaveWorks(self, server_name, channel_name, leave_message=""):

        t = time.time()
        self.proxy.channel_leave(server_name, channel_name, leave_message)
        channels = self.proxy.channel_list(server_name)
        self.assertFalse(channel_name in channels)
        self.assertMatchingEvent({
            'type': 'channel_leave',
            'server': server_name,
            'channel': channel_name,
            'text': leave_message,
        }, since=t)

    def assertLeaveFails(self, server_name, channel_name, leave_message=""):

        channels = self.proxy.channel_list(server_name)
        if channel_name in channels:
            inspect_channel_list = True
        else:
            inspect_channel_list = False

        t = time.time()
        self.assertRaises(xmlrpclib.Fault, self.proxy.channel_leave,
                          server_name, channel_name, leave_message)
        if inspect_channel_list:
            channels = self.proxy.channel_list(server_name)
            self.assertFalse(channel_name in channels)
        self.assertNoMatchingEvent({
            'type': 'channel_leave',
            'server': server_name,
            'channel': channel_name,
        }, since=t)

    ###################### Test Cases ######################

    def test_server_connect_disconnect(self):

        # Failed connections
        self.assertConnectFails(2, "pirc_test_user1")
        self.assertConnectFails("server1", 2)
        self.assertConnectFails("server1", 2, "example.com")

        # Failed disconnects
        self.assertDisconnectFails("non-existant")
        self.assertDisconnectFails(2)
        self.assertDisconnectFails("")

        # Connect and disconnect
        self.assertConnectWorks("server1", "pirc_test_user1")
        # Duplicate server names should error
        self.assertConnectFails("server1", "pirc_test_user1")
        self.assertDisconnectWorks("server1", "kthxbye")

    def test_channel_join_leave(self):

        self.assertConnectWorks("server1", "pirc_test_user1")

        # Simple join and leave
        self.assertJoinWorks("server1", "#test")
        self.assertLeaveWorks("server1", "#test")

        # Bad server names
        self.assertJoinFails("non-existant", "#test")
        self.assertJoinFails(400, "#test")

        # Bad channel names
        self.assertJoinFails("server1", "noprefix")
        self.assertJoinFails("server1", 290)

        self.assertDisconnectWorks("server1", "kthxbye")

    def test_channel_list(self):
        raise NotImplementedError()

    def test_chat(self):
        raise NotImplementedError()

        '''
        # Connect to the same server twice.  This should work!
        self.assertConnectWorks("connection1", "pirc_test_user1")
        self.assertConnectWorks("connection2", "pirc_test_user2")

        self.proxy.channel_message("connection1"

        self.assertDisconnectWorks("connection1")
        self.assertDisconnectWorks("connection2")
        '''

    def test_method_dispatch(self):
        raise NotImplementedError()
        # Test correct dispatching, and disallowing of private methods.


if __name__ == "__main__":
    process = start_proxy_process()
    try:
        unittest.main()
    finally:
        process.terminate()

