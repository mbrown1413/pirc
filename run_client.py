
from client import IRCClient, interfaces

#TODO: Make this a neat command line interface
if __name__ == "__main__":
    interface = interfaces.CursesInterface()
    client = IRCClient(
        interface, 
        proxy_address="http://localhost",
        proxy_port=2939,
    )
    client.run()
