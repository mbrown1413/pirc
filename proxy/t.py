
import xmlrpclib
import time

from tests import start_proxy_process, get_xmlrpc_client

def test():
    proxy1 = get_xmlrpc_client(port=2504)
    proxy1.server_connect("server", "nick4", "localhost")
    proxy1.channel_join("server", "#test")

    proxy2 = get_xmlrpc_client(port=2501)
    proxy2.server_connect("server", "nick2", "localhost")
    proxy2.channel_join("server", "#test")

    import pdb; pdb.set_trace()

    proxy1.channel_message("server", "#test", "Test Message!")
    proxy2.channel_message("server", "#test", "Test Message!")

if __name__ == "__main__":
    process1 = start_proxy_process(bind_port=2504)
    process2 = start_proxy_process(bind_port=2501)
    try:
        test()
    finally:
        process1.terminate()
        process2.terminate()
