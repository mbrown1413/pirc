
from errors import ServerError

def type_check(var_name, var_value, *var_types):
    '''Raises a ServerError if var_value's type is not in var_types.'''

    for var_type in var_types:
        if isinstance(var_value, var_type):
            return True

    raise ServerError('Expected "%s" type for "%s".  Got "%s" instead. '
        'Value was: %s"' % (var_type, var_name, type(var_value),
        var_value))

