
import sys

from client import IRCProxyClient
from client import interfaces
from common import config

if __name__ == "__main__":

    try:
        conf = config.ConfigParser("conf/client.conf", [
            ("cert_file", basestring, config.REQUIRED),
            ("key_file", basestring, None),
            ("accepted_certs_file", basestring, None),
            ("proxy_address", basestring, "http://localhost"),
            ("proxy_port", int, 2939),
        ])
    except conf.ConfigError as e:
        print "Error in configuration:", e
        import pdb; pdb.set_trace() #XXX
        sys.exit(1)

    client = IRCProxyClient(conf)
    interface = interfaces.WXInterface(client)
    client.run(interface)

