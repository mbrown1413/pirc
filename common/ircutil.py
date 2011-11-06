
def chan_validate(channel_name):
    '''Returns the channel_name.  Raises ValueError if name is invalid.

    Validation is done according to RFC 1459 section 1.3.  The channel name is
    made lower case before validation, and returned as lower case.

    '''
    channel_name = channel_name.lower()  # case insensitive channel names
    if len(channel_name) <= 2 or len(channel_name) > 50 or \
            channel_name[0] not in "&#+!" or \
            ": ,"+chr(7) in channel_name:
        raise ValueError('Invalid channel name: "%s".' % channel_name)
    return channel_name

def nick_split(full_nick):
    '''Returns (nick, location) given a nickname "nick!location".

    location will be an empty string if it isn't present in the input.  Raises
    a ValueError for an invalid nickname.

    '''
    split = full_nick.split('!')
    nick = split[0]
    if len(split) == 2:
        location = split[1]
    elif len(split) == 1:
        location = ""
    else:
        raise ValueError('Invalid Nickname: "%s".' % full_nick)
    return nick, location
