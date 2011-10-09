
"""XMLRPC client and server support for SSL, and certificate checking.

TODO: Document what happens when a certificate is invalid or not provided.

======
Server
======

The secure server is provided in `SecureXMLRPCServer`.  Usage is similar to
`SimpleXMLRPCServer`, but there are some extra arguments to allow for
certificate checking.  Here is a complete server example::

    from securexmlrpc import SecureXMLRPCServer

    def xmlrpc_func(text):
        print text
        return "Hello from server"

    server = SecureXMLRPCServer(
        ("localhost", 10023),
        certfile="server.pem",
        ca_certs="server_trusted.pem",
    )
    server.register_function(xmlrpc_func)
    server.serve_forever()

In the example, the server will use the certificate and private key stored in
the file "server.pem" and it will only accept clients that use one of the
certificates stored in "server_trusted.pem".


======
Client
======

For a certificate checking SSL client, a transport method is implemented in
`HTTPSTransport`.  To use it, create an instance then pass it into
`xmlrpclib.ServerProxy`.  Here is a complete client example::

    import xmlrpclib
    import securexmlrpc

    transport = securexmlrpc.HTTPSTransport(
        certfile = "client.pem",
        ca_certs = "client_trusted.pem",
    )
    proxy = xmlrpclib.ServerProxy("https://localhost:10023", transport)
    print proxy.xmlrpc_func("Hello from client")

In the example, the client will use the certificate and private key stored in
the file "client.pem" and it will only connect to servers that use one of the
certificates listed in "client_trusted.pem".


============
Certificates
============

The Python documentation on the ssl module has a good section on certificate
formats, and how to generate them.  I will summarize and fill in some details here.

The openssl command to generate a self signed certificate::

    openssl req -new -x509 -days 365 -nodes -out client.pem -keyout client.pem

"client.pem" should be replaced by a filename you wish to create.  You can
specify a different keyout to store the private key in a different file if you
like.  In this case, you would pass the "keyfile" keyword argument to
`HTTPSTransport` and `SecureXMLRPCServer`, specifying the file with the private
key.

The in the examples above, the *_trusted.pem files contains certificates for
trusted certificate authorities.  For our purposes (because our certificates
are self signed) they just contain a list of certificates which are trusted.
To create one of these files, copy the section from a certificate between (and
including) the lines "-----BEGIN CERTIFICATE-----" and
"-----END CERTIFICATE-----".


"""

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpclib
import httplib
import socket
import ssl

__all__ = [
    "SecureXMLRPCServer",
    "HTTPSTransport",
    "HTTPSConnection",
]

class SecureXMLRPCServer(SimpleXMLRPCServer):
    """XMLRPC Server that uses HTTPS and checks certificates."""

    def __init__(self, *args, **kwargs):
        """
        Takes the same arguments as SimpleXMLRPCServer, with the addition of
        some keyward arguments documented here.  All of the additional
        arguments are passed directly into `ssl.wrap_socket`.  For details, see
        the documentation on `ssl.wrap_socket`.

        :param certfile:
            File with PEM formatted certificate.

        :param keyfile:
            File with PEM formatted private key.  Not needed if certfile
            contains private key.

        :param cert_reqs:
            Specifies whether a certificate is required from clients.  Must be
            one of `ssl.CERT_OPTIONAL`, `ssl.CERT_REQUIRED`, or
            `ssl.CERT_NONE`.  Default `ssl.CERT_REQUIRED`.

        :param ca_certs:
            File containing accepted "certification authority" certificates.

        :param ssl_version:
            SSL version to use.  Must be one of `ssl.PROTOCOL_*`.  Default
            `ssl.PROTOCOL_TLSv1`.
        """

        self.keyfile = kwargs.pop("keyfile", None)
        self.certfile = kwargs.pop("certfile", None)
        self.cert_reqs = kwargs.pop("cert_reqs", ssl.CERT_REQUIRED)
        self.ca_certs = kwargs.pop("ca_certs", None)
        self.ssl_version = kwargs.pop("ssl_version", ssl.PROTOCOL_TLSv1)
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    def get_request(self):
        """
        Same as SimpleXMLRPCServer.get_request, but it uses ssl and checks
        certificates.
        """
        newsocket, fromaddr = self.socket.accept()
        sslsocket = ssl.wrap_socket(newsocket,
                                    server_side = True,
                                    keyfile = self.keyfile,
                                    certfile = self.certfile,
                                    cert_reqs = self.cert_reqs,
                                    ca_certs = self.ca_certs,
                                    ssl_version = ssl.PROTOCOL_TLSv1)
        return sslsocket, fromaddr

class HTTPSConnection(httplib.HTTPConnection):
    """
    Like httplib.HTTPSConnection, but optionally checks certificate of server.
    """

    default_port = httplib.HTTPS_PORT

    def __init__(self, host, port=None, keyfile=None, certfile=None,
                 cert_reqs=ssl.CERT_REQUIRED, ca_certs=None, strict=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
        httplib.HTTPConnection.__init__(self, host, port, strict, timeout,
                                        source_address)
        self.keyfile = keyfile
        self.certfile = certfile
        self.cert_reqs = cert_reqs
        self.ca_certs = ca_certs

    def connect(self):
        """
        Same as httplib.HTTPSConnection, but passes extra arguments into
        ssl.wrap_socket that tell it to check certificates.
        """

        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(
            sock,
            keyfile = self.keyfile,
            certfile = self.certfile,
            cert_reqs = self.cert_reqs,
            ca_certs = self.ca_certs,
        )

class HTTPSTransport(xmlrpclib.Transport):
    """XMLRPC Transport subclass for HTTPS that checks certificates.

    To use this, instantiate it and pass it into xmlrpclib.ServerProxy like
    this::

        import xmlrpclib
        import securexmlrpc

        transport = securexmlrpc.HTTPSTransport(
            cert_file = "client.pem",
            ca_certs = "client_trusted.pem",
        )
        proxy = xmlrpclib.ServerProxy("https://localhost:10023", transport)

    """

    def __init__(self, certfile=None, keyfile=None, ca_certs=None,
                 use_datetime=0):
        """
        The same as httplib.HTTPTransport, but takes some extra arguments that
        allow for certificate checking.  These extra arguments are passed
        directly into `ssl.wrap_socket`.

        :param certfile:
            File with PEM formatted certificate.

        :param keyfile:
            File with PEM formatted private key.  Not needed if certfile contains
            private key.

        :param ca_certs:
            File containing accepted "certification authority" certificates.

        :param use_datetime:
            Same as `httplib.HTTPTransport`.

        """

        xmlrpclib.Transport.__init__(self, use_datetime)
        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs

    def make_connection(self, host):
        """
        Same as xmlrpclib.Transport.make_connection, but it uses
        HTTPSConnection (which checks certificates).
        """
        if self._connection and host == self._connection[0]:
            return self._connection[1]
        chost, self._extra_headers, x509 = self.get_host_info(host)
        self._connection = host, HTTPSConnection(
            chost,
            None,
            keyfile = self.keyfile,
            certfile = self.certfile,
            ca_certs = self.ca_certs,
        )
        return self._connection[1]

