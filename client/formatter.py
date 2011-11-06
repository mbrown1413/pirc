
from common import ircutil

class Formatter(object):
    '''
    Formats events into human readable text.
    '''

    def __init__(self, client):
        self.client = client

    def print_event(self, event):

        print_method = getattr(self, "print_event_"+event['type'], None)
        if print_method:
            text = print_method(event)
        else:
            #TODO: Log
            print "Warning: Event with no formatter: " + event['type']
            text = None

        if text:
            server = None
            channel = None
            if 'server' in event:
                server = event['server']
            if 'target' in event:
                channel = event['target']
            self.client.put_text(server, channel, text)

    ################# Print Methods #################

    def print_event_pubmsg(self, event):
        return "<%s>: %s\n" % (event['source'].split("!")[0], event['text'])
    print_event_privmsg = print_event_pubmsg

    def print_event_welcome(self, event):
        return "%s: %s\n" % (event['type'], event['text'])
    print_event_created = print_event_welcome
    print_event_luserlist = print_event_welcome
    print_event_motd = print_event_welcome

    def print_event_channel_join(self, event):
        return "%s joined %s\n" % (event['user'], event['target'])

    def print_event_channel_part(self, event):
        return "%s left %s\n" % (event['user'], event['target'])
