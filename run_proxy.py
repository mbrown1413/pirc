
from proxy import IRCProxy

#TODO: Make this a neat command line interface
if __name__ == "__main__":
    proxy = IRCProxy(
        bind_address="localhost",
        bind_port=2939,
    )
    proxy.run()
