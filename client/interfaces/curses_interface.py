
import curses
from curses import textpad

class CursesInterface(object):

    def __init__(self):
        pass

    def init(self, client):
        self.client = client

        # Set curses settings
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        try: # Try to get color support
            curses.start_color()
        except:
            pass

        # Create Windows
        height, width = self.stdscr.getmaxyx()

        self.chat_win = curses.newwin(height-2, width, 0, 0)
        self.chat_win.scrollok(True)

        self.type_win = curses.newwin(1, width, height-1, 0)
        self.type_win.nodelay(1)

        self.status_win = curses.newwin(1, width, height-2, 0)
        self.textbox = textpad.Textbox(self.type_win)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.status_win.addstr(0, 0, " "*(width-1), curses.color_pair(1))
        self.status_win.redrawwin()
        self.status_win.refresh()

    def uninitialize(self):

        # Set terminal settings to normal
        if hasattr(self, "stdstr"):
            self.stdscr.keypad(0)
        print curses
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def on_event(self, event):
        if event['type'] == "pubmsg" or event['type'] == "privmsg":
            height, width = self.chat_win.getmaxyx()
            self.chat_win.scroll(1)
            text = "<%s>: %s" % (event['source'].split("!")[0], event['arguments'][0])
            self.chat_win.addstr(height-1, 0, str(text))
            (y, x) = self.type_win.getyx()
            self.chat_win.refresh()

    def get_command(self, timeout=0):
        self.type_win.timeout(timeout)
        if not self.textbox.do_command(self.type_win.getch()):
            command = self.textbox.gather()
            self.client.do_command("127.0.0.1", "#main", command)
            self.type_win.deleteln()
            self.type_win.move(0, 0)
            self.type_win.refresh()
