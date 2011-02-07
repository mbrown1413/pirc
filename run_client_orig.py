
import xmlrpclib
from time import time, sleep
import curses
from curses import textpad

def main(stdscr):

    proxy = xmlrpclib.ServerProxy("http://localhost:2939/")
    from random import randint
    #proxy.connect("127.0.0.1", 6667,  "Client"+str(randint(0,99999)))
    #proxy.join("127.0.0.1", "#main")

    height, width = stdscr.getmaxyx()
    chat_win = curses.newwin(height-2, width, 0, 0)
    type_win = curses.newwin(1, width, height-1, 0)
    status_win = curses.newwin(1, width, height-2, 0)
    type_win.nodelay(1)
    textbox = textpad.Textbox(type_win)
    chat_win.scrollok(True)

    # Status Text
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    status_win.addstr(0, 0, " "*(width-1), curses.color_pair(1))
    status_win.redrawwin()
    status_win.refresh()

    last_event_time = 0.0
    while True:
        events = proxy.get_events_since(last_event_time)
        if events:

            for event in events:
                if last_event_time < event['time']:
                    last_event_time = event['time']

                if event['type'] == "pubmsg" or event['type'] == "privmsg":
                    height, width = chat_win.getmaxyx()
                    chat_win.scroll(1)
                    text = "<%s>: %s" % (event['source'].split("!")[0], event['arguments'][0])
                    chat_win.addstr(height-1, 0, str(text))
                    (y, x) = type_win.getyx()
                    type_win.move(y, x)

            chat_win.refresh()
        if not textbox.do_command(type_win.getch()):
            message = textbox.gather()
            proxy.privmsg("127.0.0.1", "#main", message)
            type_win.deleteln()
            type_win.move(0, 0)
            type_win.refresh()

        sleep(0.1)

    '''
    height, width = stdscr.getmaxyx()
    stdscr.move(height-1, 0)
    stdscr.scrollok(True)
    i=0
    while True:
        stdscr.move(height-1, 0)
        stdscr.addstr("Hello %s" % i)
        stdscr.refresh()
        i += 1
        sleep(1)
        stdscr.scroll(1)
    '''

if __name__ == "__main__":
    curses.wrapper(main)
