
import unittest
from StringIO import StringIO

__all__ = ['REQUIRED', 'ANY_TYPE', 'ConfigParser', 'ConfigError']

REQUIRED = object()
ANY_TYPE = object

class ConfigError(Exception):
    pass

class ConfigParser(object):
    """Parse config files that are just python scripts in disguise.

    A list of options are given in the constructor, and only these options are
    made available to the user, even if more were defined in the config file.
    Options are accessed as an attribute of the instantiated object::

        conf = ConfigParser("this.conf", [("foo", basestring, REQUIRED)])
        print conf.foo

    Config files are just python scripts run using python's exec statement.
    This allows config files to be very dynamic.

    """

    def __init__(self, config_file, options):
        """
        :param config_file:
            This can either be a path to the config file, or a file (like)
            object containing the config file text.  Any strings (anything
            derived from basestring) will be interpreted as a filename, and
            anything else will be interpreted as a file object.  File objects,
            of course, need to be closed by the user afterwards if desired.

        :param options:
            A list of 3 tuples: (name, type, default).  After the config file
            is parsed, an option of the given name is looked for.  Option names
            cannot start with an underscore.  If it isn't found and default is
            REQUIRED, a ConfigError is raised.  If type is not ANY_TYPE, then
            the config value will be checked to make sure it is an instance of
            that type.

        """

        # Read config file.
        # This fills the variables dict with any variables that were assigned when
        # executing the file.
        variables = {}
        if isinstance(config_file, basestring):
            execfile(config_file, {}, variables)
        else:
            exec(config_file.read(), {}, variables)

        # Record all unused variables in config file.
        # Used later in __getattr__ to distinguish two different error messages.
        # Variables are popped from this list when they are parsed.
        self._unused_variables = variables.keys()

        self._config = {}
        for opt_name, opt_type, opt_default in options:

            # Error check
            if opt_name.startswith('_'):
                raise ConfigError('Configuration options cannot start with an underscore.')
            elif opt_name in variables and not isinstance(variables[opt_name], opt_type):
                raise ConfigError('Configuration option "%s" should be of type "%s".  It is type "%s" instead.' % (opt_name, opt_type, type(variables[opt_name])))
            elif opt_name not in variables and opt_default is REQUIRED:
                raise ConfigError('Required configuration option "%s" is missing!' % opt_name)

            # Assign self._config[opt_name]
            elif opt_name in variables:
                self._config[opt_name] = variables[opt_name]
                self._unused_variables.remove(opt_name)
            elif opt_name not in variables:
                self._config[opt_name] = opt_default

    def __getattr__(self, name):
        if name not in self._config:
            if name in self._unused_variables:
                raise ValueError('The config parser does not allow option "%s", even though it exists in the config file.' % name)
            else:
                raise ValueError('Config option not found: "%s".' % name)
        return self._config[name]


class TestConfig(unittest.TestCase):

    def test_syntax_error(self):
        self.assertRaises(SyntaxError,
            ConfigParser, StringIO("parse:error"), [])

    def test_basic(self):
        config = ConfigParser(
            StringIO("opt1 = 1; opt2 = 'a'"),
            [
                ("opt1", int, 2),
                ("opt2", basestring, 'b'),
            ]
        )
        self.assertEquals(config.opt1, 1)
        self.assertEquals(config.opt2, 'a')
        self.assertRaises(ValueError, lambda:config.extraneous)

    def test_extraneous_option(self):
        config = ConfigParser(
            StringIO(""),
            []
        )
        self.assertRaises(ValueError, lambda:config.extraneous)

    def test_typecheck(self):
        self.assertRaises(ConfigError,
            ConfigParser,
            StringIO("opt1 = 2"),
            [("opt1", basestring, REQUIRED)]
        )

    def test_required_option(self):
        self.assertRaises(ConfigError,
            ConfigParser,
            StringIO("opt1 = 2"),
            [("nonexistant", basestring, REQUIRED)]
        )

    def test_default_option(self):
        config = ConfigParser(
            StringIO("opt1 = 2"),
            [
                ("opt1", int, REQUIRED),
                ("opt2", basestring, 'b'),
            ]
        )
        self.assertEquals(config.opt1, 2)
        self.assertEquals(config.opt2, 'b')

    def test_any_type(self):
        config = ConfigParser(
            StringIO("opt1 = 2"),
            [("opt1", ANY_TYPE, REQUIRED)]
        )
        self.assertEquals(config.opt1, 2)

        config = ConfigParser(
            StringIO("opt1 = 'THISISASTRING'"),
            [("opt1", ANY_TYPE, REQUIRED)]
        )
        self.assertEquals(config.opt1, 'THISISASTRING')

if __name__ == '__main__':
    unittest.main()
