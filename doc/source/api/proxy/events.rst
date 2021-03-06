
Events
============================================

What is an event?
-----------------
Interactions with IRC servers are recorded in the form of events.  All events
are plain dictionaries.  This format was chosen so they may be passed freely
via XMLRPC.  One example of an event is "pubmsg", which records what somebody
has said in an IRC channel.  This event is usually recorded when a message
comes from the IRC server, but when the client sends a message to the server,
the proxy server records the message instead.

Events are stored on the proxy server.  When a proxy client starts, it will ask
for all events, then replay those events in order.

Event Format
------------
Every event is a dictionary.  These fields are guaranteed to have these fields:

* time: The server time, in seconds since UNIX epoch, which the event was recorded.
* type: A string identifying the type of event.

.. todo:: Document all events

pubmsg / privmsg
````````````````
Generated when any somebody says something in a channel that the user is
connected to.  Also generated by the proxy server when the user sends a message
to an IRC server.

Additional fields:
* server: server_identifier
* source: source_destination_identifier
* target: source_destination_identifier
* text: String of the message sent.

server_connect
``````````````
* server: server_identifier

channel_join / channel_leave
````````````````````````````


irc_error
`````````
