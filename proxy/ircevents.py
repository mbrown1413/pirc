
import time

def format_irc_event(irc_event, proxy_client):

    if irc_event._eventtype in EVENT_TYPE_FORMATTERS:
        format_func = EVENT_TYPE_FORMATTERS[irc_event._eventtype]
    else:
        raise ValueError("Unhandled event type:%s\nEvent was:%s" % (irc_event._eventtype, irc_event))

    return format_func(irc_event, proxy_client)

def format_msg(irc_event, proxy_client):
    return {
        'type': irc_event._eventtype,
        'server': get_event_server_name(irc_event, proxy_client),
        'source': irc_event._source,
        'target': irc_event._target,
        'text': irc_event._arguments[0],
    }

def format_server_message(irc_event, proxy_client):
    return {
        'type': irc_event._eventtype,
        'server': get_event_server_name(irc_event, proxy_client),
        'text':irc_event._arguments[0],
    }

def format_server_join(irc_event, proxy_client):
    return {
        'type': irc_event._eventtype,
        'server': get_event_server_name(irc_event, proxy_client),
    }

def get_event_server_name(irc_event, proxy_client):

    connection = irc_event.connection
    for server in proxy_client.remote_irc_servers.itervalues():
        if server.connection == connection:
            return server.server_name

def format_ignore(irc_event, proxy_client):
    return False

EVENT_TYPE_FORMATTERS = {

    # Channel Messages
    'privmsg': format_msg,
    'pubmsg': format_msg,

    # Server Messages
    'motd': format_server_message,
    'startmotd': format_server_message,
    'luserconns': format_server_message,
    'luserchannels': format_server_message,
    'privnotice': format_server_message,
    'server_join': format_server_join,

    #TODO:
    'join': format_ignore,
    'namreply': format_ignore,
    'endofnames': format_ignore,
    'umode': format_ignore,
    'motdstart': format_ignore,
    'endofmotd': format_ignore,
    'luserclient': format_ignore,
    'luserme': format_ignore,
    'featurelist': format_ignore,
    'n_local': format_ignore,
    'n_global': format_ignore,
    'myinfo': format_ignore,
    'welcome': format_ignore,
    'yourhost': format_ignore,
    'created': format_ignore,
    'error': format_ignore,
    'disconnect': format_ignore,

}

