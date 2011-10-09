
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
    elif argv[1] == "client":
        cert_file = "client_cert.pem"
        key_file = "client_key.pem"
    else:
        usage()

    current_dir = path.realpath(path.join(__file__, "../"))
    cert_file = path.join(current_dir, cert_file)
    key_file = path.join(current_dir, key_file)

    generate_x509(cert_file, key_file)

    print
    print "Cert generated:", cert_file
    print "Key generated:", key_file
    print """
After creating proxy and client certificates, you need to make the proxy and
client trust eachother.  To do this, copy "proxy_cert.pem" to
"client_accepted_certs.pem" and copy "client_cert.pem" to
"proxy_accepted_certs.pem".
"""

