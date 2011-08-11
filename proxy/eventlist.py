
import time

class EventList(object):

    def __init__(self):
        self.events = []

    def append(self, event=None, **kwargs):
        if event:
            self.events.append(event)

        else:

            if "type" not in kwargs:
                raise ValueError("Event must have a type."
                                 "Erronous event: %s" % kwargs)
            if "time" not in kwargs:
                kwargs["time"] = time.time()
            if "server" not in kwargs:
                kwargs["server"] = False
            self.append(kwargs)

    def get_event_slice(self, start_index, end_index):
        '''Get a slice of events.

        begin and end are indexes into the event list, with index 0 being the
        latest event.

        Example: This will get the latest 10 events:
        >>> channel.get_event_slice("irc.example.com", 0, 10)

        '''
        return self.events[::-1][start_index:end_index][::-1]

    def get_events_since(self, start_time):
        event_list = []
        for event in self.events[::-1]:
            if event["time"] <= start_time:
                return event_list
            else:
                event_list.append(event)
        return event_list
