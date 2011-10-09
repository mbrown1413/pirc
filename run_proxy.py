
from proxy import IRCProxyServer
from common import config

if __name__ == "__main__":

    try:
        conf = config.ConfigParser("conf/proxy.conf", [
            ("cert_file", basestring, config.REQUIRED),
            ("key_file", basestring, None),
            ("accepted_certs_file", basestring, None),
            ("bind_address", basestring, "0.0.0.0"),
            ("bind_port", int, 2939),
        ])
    except conf.ConfigError as e:
        raise #TODO

    proxy = IRCProxyServer(conf)
    proxy._run()

