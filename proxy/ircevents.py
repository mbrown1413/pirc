
import time

from common import ircutil

def format_irc_event(irc_event, proxy_client):

    try:
        irc_event._eventtype = int(irc_event._eventtype)
    except ValueError: pass

    if isinstance(irc_event._eventtype, int):
        format_func = format_error

    elif irc_event._eventtype in EVENT_TYPE_FORMATTERS:
        format_func = EVENT_TYPE_FORMATTERS[irc_event._eventtype]

    else:
        event_dict = {
            '_eventtype': irc_event._eventtype,
            '_source': irc_event._source,
            '_target': irc_event._target,
            '_arguments': irc_event._arguments,
        }
        raise ValueError("Unknown event type: %s\nEvent was: %s" % (irc_event._eventtype, event_dict))

    return format_func(irc_event, proxy_client)


def format_error(irc_event, proxy_client):
    return {
        'type': 'irc_error',
        'server': get_server(irc_event, proxy_client).server_name,
        'text': u' '.join(irc_event._arguments),
    }

def format_msg(irc_event, proxy_client):
    return {
        'type': irc_event._eventtype,
        'server': get_server(irc_event, proxy_client).server_name,
        'source': irc_event._source,
        'target': irc_event._target,
        'text': irc_event._arguments[0],
    }

def format_server_message(irc_event, proxy_client):
    return {
        'type': irc_event._eventtype,
        'server': get_server(irc_event, proxy_client).server_name,
        'text': irc_event._arguments[0],
    }

def format_server_join(irc_event, proxy_client):
    return {
        'type': 'server_connect',
        'server': get_server(irc_event, proxy_client).server_name,
    }

def format_channel_join_part(irc_event, proxy_client):
    server = get_server(irc_event, proxy_client)
    user, location = ircutil.nick_split(irc_event._source)
    return {
        'type': 'channel_%s' % irc_event._eventtype,
        'server': server.server_name,
        'target': irc_event._target,
        'user': irc_event._source,
        'this_user': server.nick_name == user,
    }

def get_server(irc_event, proxy_client):
    connection = irc_event.connection
    for server in proxy_client.remote_irc_servers.itervalues():
        if server.connection == connection:
            return server

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
    'join': format_channel_join_part,
    'part': format_channel_join_part,

    #TODO:
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
    'nosuchchannel': format_ignore,
    'mode': format_ignore,

}

