
====
PIRC
====

Pirc is an IRC client with two distinct parts:

* Proxy Server - Runs on a server that is always on, allowing it to stay
  connected to IRC servers even while the proxy client is not running.
* Proxy Client - Connects to the proxy server from the user's computer.  Gets
  events from the proxy server that may have happened while no proxy client was
  running.

This model allows proxy clients to start, stop, suspend or crash without
loosing any data or disconnecting from an IRC server.  It also allows a user to
stay inside an IRC channel while not running a proxy client.


Status
------
Pirc is usable at the moment, but still under heavy development.  The server is
well documented, but the all of the docs need to be compiled with Sphinx.  The
client commands need to be cleaned up and documented.  I'm happy with how the
first draft of the user interface (a wxwidgets interface) turned out, but it is
still somewhat rudimentary.


Documentation
-------------
TODO: Commit Sphinx documentation, set up readthedocs, and link to it here.

