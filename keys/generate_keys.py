
import subprocess
from os import path
from sys import argv, exit

def generate_x509(cert_file, key_file):
    try:
        subprocess.check_call((
            "openssl", "req", "-new", "-x509", "-nodes",
            "-days", "365",
            "-out", cert_file,
            "-keyout", key_file))
    except OSError as e:
        raise #TODO
    except subprocess.CalledProcessError as e:
        raise #TODO

def usage(message=None):
    if message:
        print message
    print "Usage:"
    print "    python %s client" % argv[0]
    print "  Or:"
    print "    python %s proxy" % argv[0]
    exit(1)

if __name__ == '__main__':

    # Parse Arguments
    if len(argv) != 2:
        usage("Wrong number of arguments.")
    elif argv[1] == "proxy":
        cert_file = "proxy_cert.pem"
        key_file = "proxy_key.pem"
        ca_certs_file = "proxy_accepted_certs.pem"
    elif argv[1] == "client":
        cert_file = "client_cert.pem"
        key_file = "client_key.pem"
        ca_certs_file = "client_accepted_certs.pem"
    else:
        usage()

    current_dir = path.realpath(path.join(__file__, "../"))
    cert_file = path.join(current_dir, cert_file)
    key_file = path.join(current_dir, key_file)
    ca_certs_file = path.join(current_dir, ca_certs_file)

    generate_x509(cert_file, key_file)

    # Create ca_certs_file
    if not path.exists(ca_certs_file):
        open(ca_certs_file, 'w').close()

    print
    print "Cert generated:", cert_file
    print "Key generated:", key_file
    if argv[1] == "proxy":
        print """
Now you should copy your client's certificate file into %s, so the proxy will
accept the client's connections.
""" % ca_certs_file
    elif argv[1] == "client":
        print """
Now you should copy your proxy's certificate file into %s, so the client will
trust the proxy and be able to connect to it.
""" % ca_certs_file

