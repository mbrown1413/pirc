
XML-RPC Interface
============================================

The proxy XML-RPC interface is used by the proxy client component to talk to
the proxy server.  Since XML-RPC is language agnostic, the proxy client could
be written in any language (for more information see the `XML-RPC website
<http://www.xmlrpc.com/>`_).  The standard implementation is written in Python.

The interface is based on the idea of events.  The server keeps a list of
events, which can be retrieved by the client with :func:`get_events_since`.
When a client causes an action to be performed by the proxy, an event is
generated.  The client should not respond to this action until it actually
receives the event.  This allows clients to be restarted without losing any
state.  The client simply needs to request a list of all events on
initialization.


Error Handling
--------------
Error handling is done through XML-RPC faults.  Faults are handled
differently, depending on the XML-RPC library.   The proxy is synchronous
(completes the whole action before returning from a method), so faults are
always returned in the XML-RPC method in which the error occurred.

If any known error occurs then a fault with faultCode 2 is returned, with a
faultString explanation of the error.  A common example of a known error is an
invalid parameter passed to an XML-RPC method.

If any unknown error occurs in the server, a fault with faultCode 3 is
returned.  The faultString explains that an internal server error occurred.
These are the signs of a bug in the proxy server.  The underlying exception
that caused the error in the proxy server will be logged.

Most faultStrings are suitable to be read by the end user.  If a faultString
does not make sense to the end user, it probably means the client is not using
the interface correctly.


Common Parameters
-----------------
There are some parameters which are used in many different methods.  Those
parameters are documented here to reduce redundancy:

* server_name - A string initially provided by the client in
  :func:`server_connect`.  The same string is then used in other methods to
  reference the server.
* channel_name - A name of a channel that the method acts upon or references.
  Valid channel names start with '#' or '&' (a complete description of valid
  channel names can be found in RFC 1459 section 1.3).


Methods
-------
.. todo:: Reference events that are created by these methods.

.. function:: get_events_since(start_time)

    Return events that have happened since `start_time`.

    Commonly used by clients to first get all events (by calling passing
    `start_time=0`) then getting any new events (by passing `start_time =
    <last event time>`) in an endless loop.

    :param start_time:
        Only events occurring after this time are returned.  Format is in
        seconds since Unix epoch.

    :returns:
        An array of :doc:`event structures <events>`.  The events are *not*
        guaranteed to be in the correct order.

.. function:: server_list()

    List server names that are connected.

    :returns:
        An array of server names.

.. function:: server_connect(server_name, nick_name, uri, port=6667, password="", ssl=False, ipv6=False)

    Connect to an IRC server.

    The client can then join a channel in this server with
    :func:`channel_join`.

    :param nick_name:
        User nick name to present to the server.

    :param uri:
        URI of the server.

    :param port:
        Port number of the server.  Default 6667.

    :param password:
        Password, if any, to present to the server.  Empty string if none.

    :param ssl:
        If True, ssl is used to connect to the server.

    :param ipv6:
        If True, ipv6 is used to connect to the server.

.. function:: server_disconnect(server_name, leave_message="")

    Disconnect from an IRC server.

    :param leave_message:
        A message that is given to each channel and the server when
        leaving.

.. function:: channel_list(server_name)

    List channels in this server that the user is currently in.

    :returns:
        An array of channel names.

.. function:: channel_join(server_name, channel_name)

    Join a channel.

.. function:: channel_leave(server_name, channel_name, message="")

    Leave a channel.

    :param message:
        A message that is given to the channel as a reason for leaving.

.. function:: channel_message(server_name, channel_name, message)

    Send a message to a channel.

    :param message:
        The text to send to the channel.
