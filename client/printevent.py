
def print_event(event, interface):
    print event
    if event['type'] in EVENT_PRINTERS:
        print_func = EVENT_PRINTERS[event['type']]
        print_func(event, interface)
    else:
        #TODO: Log
        print "Event has no print:", event['type']

def print_msg(event, interface):
    interface.put_text(event['server'], event['target'],
        "<%s>: %s\n" % (event['source'], event['text']))

EVENT_PRINTERS = {
    'privmsg': print_msg,
    'pubmsg': print_msg,
}

