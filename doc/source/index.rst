.. Proxy IRC Client documentation master file, created by
   sphinx-quickstart on Wed Aug  3 12:32:26 2011.

PIRC documentation
============================================

PIRC stands for Proxy IRC.  PIRC has two components: the local client, and the
proxy.  The proxy normally runs on another server, and the client runs on your
local machine.  As long as the proxy is running, it stays connected to your IRC
servers and records messages and other events.  When your local client
connects, it can grab the events that happened when it was shut down.

PIRC was created as an alternative to using ssh, GNU screen and irssi.

Contents:

.. toctree::
    :maxdepth: 2

    tutorial
    api/index
    todo

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
