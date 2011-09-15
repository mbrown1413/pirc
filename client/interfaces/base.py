
class BaseInterface(object):
    '''Base class for an irc client user interface.

    The implementor has quite a bit of freedom in how the display works.

    Methods which raise a `NotImplemented` error must be implemented.  All other
    methods are optional.

    An interface has to follow the basic text input and output model::

    * When text is entered by the user (a command or message) the interface
      should call `client.run_command`.  Associated server and channel should
      be given when applicable.
    * When text is output to the user, `interface.put_text` is called by the
      client object.  An appropriate server and channel will be given if
      applicable.

    The interface has the main control loop of the application.  The interface
    must call `self.client.handle_events` periodically for any events to be
    received.

    '''

    def __init__(self, client):
        '''
        May be overwritten, but `BaseInterface.__init__` must be called at the
        beginning.  Unless there is a good reason, the interface should use
        `initialize` instead of this.
        '''
        self.client = client

    def initialize(self):
        '''Initializes the window or display for this interface.'''
        pass

    def uninitialize(self):
        '''Uninitializes the window or display for this interface.

        This is **always** called at the end of the program, even if
        `initialize` failed.  `uninitialize` should not break if the application
        is in an inconsistent state.  This is especially important for terminal
        text based interfaces, because things like the terminal mode needs to
        get reset properly on exit.

        '''
        pass

    def put_text(self, server, channel, text):
        '''Give some text output to the user.

        Called by the client object.

        :param server:
            The server which the text is associated with, or None.

        :param channel:
            The channel which the text is associated with, or None.

        :param text:
            Text which should be displayed to the user.  Note that a single
            line of text could be broken into multiple calls of this method.
            When a newline is appropriate, it will be present in the given
            text; no newlines should be added by `put_text`.

        .. todo:: Describe nuances of when server and channel are None.

        '''
        raise NotImplementedError("This method must be implemented.")

    def run(self):
        '''The client main loop.

        A blocking call that goes into an infinite loop waiting for user
        interface events.  When this function exits, the client closes.
        `self.client.handle_event **must** be called periodically, or IRC
        events will never be received.

        '''
        raise NotImplementedError("This method must be implemented.")

    def on_channel_join(self, server, channel):
        '''Called when a channel is joined.

        This will always be called before any text is given (with `put_text`)
        for the server channel pair.

        This is here so the interface can create a tab/window/whatever when a
        channel is joined and left.  Its up to the implementation whether this
        needs to be implemented.

        :param server:
            Server that the channel is on.

        :param channel:
            Channel which was joined.

        '''
        pass

    def on_channel_leave(self, server, channel):
        '''Called when the user leaves a channel.

        :param server:
            Server that the channel is on.

        :param channel:
            Channel which was joined.

        '''
        pass

    def set_style(self, style):
        '''
        TODO
        '''
        pass
