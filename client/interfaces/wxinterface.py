
from itertools import ifilter

import wx

from .base import BaseInterface

def _menu_name(server, channel):
    if channel:
        return "%s : %s" % (server, channel)
    else:
        return server

class WXInterface(BaseInterface):
    '''A WX Widgets irc interface.'''

    def initialize(self):

        self.current_server = None
        self.current_channel = None

        # Maps (server, channel) to the corresponding display box
        self.display_boxes = {}

        ################ Layout Setup ################
        # The layout has the following hierarchy:
        #   frame
        #     |
        #     -- horizontal_box
        #          |
        #          -- vertical_box
        #               |
        #               -- display_box
        #               |
        #               -- command_box
        #
        # The horizontal_box is present to make the contents fit the width of
        # the window.  If you know a better way, please suggest something.
        #
        # self.display_box is replaced by a textbox for the channel that is
        # currently being viewed.  It starts out as self.default_box, which is
        # replaced when the first channel is joined.

        self.app = wx.App()
        # Frame size fits 80 char width (on my computer).
        self.frame = wx.Frame(None, -1, "Pirc", size=wx.Size(565, 300))
        self.panel = wx.Panel(self.frame, -1)

        self.default_style = wx.TextAttr("black", "white", wx.Font(8,
                wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL), False)

        self.default_box = self.new_display_box()
        self.command_box = wx.TextCtrl(self.panel, -1, '',
                                       style=wx.TE_PROCESS_ENTER)

        self.vertical_box = wx.BoxSizer(wx.VERTICAL)
        self.vertical_box.Add(self.default_box, 1, wx.EXPAND)
        self.vertical_box.Add(self.command_box, 0, wx.EXPAND)

        self.horizontal_box = wx.BoxSizer(wx.HORIZONTAL)
        self.horizontal_box.Add(self.vertical_box, 1, wx.EXPAND)

        self.panel.SetSizer(self.horizontal_box)

        # Timer Setup
        # The timer will call self.client.handle_events() every so often.
        self.timer = wx.PyTimer(lambda: self.client.handle_events())
        self.timer.Start(2000)

        # Menu Setup
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        quit_item = wx.MenuItem(file_menu, -1, "&Quit\tCtrl+Q", "Quit PIRC")
        wx.EVT_MENU(self.frame, quit_item.GetId(), self.exit_callback)
        file_menu.AppendItem(quit_item)
        menubar.Append(file_menu, "&File")

        # Channels menu
        self.channel_menu = wx.Menu()
        menubar.Append(self.channel_menu, "&Channels")

        self.frame.SetMenuBar(menubar)

        # Bind Callbacks
        self.frame.Bind(wx.EVT_TEXT_ENTER, self.command_box_callback)
        self.frame.Bind(wx.EVT_CLOSE, self.exit_callback)

    def new_display_box(self):
        box = wx.TextCtrl(self.panel, -1, '', style=
                wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH |
                wx.TE_NOHIDESEL | wx.TE_LEFT)
        box.SetDefaultStyle(self.default_style)
        # Focus the command box whenever the display box is focused
        wx.EVT_SET_FOCUS(box, self.focus_command_box)
        return box

    def on_server_connect(self, server):
        self.window_create(server, None)

    def on_server_disconnect(self, server):
        channels = ifilter(lambda x: x[0]==server, self.display_boxes.iterkeys())
        for channel in channels:
            self.window_destroy(server, channel)
        self.window_destroy(server, None)

    def on_channel_join(self, server, channel):
        self.window_create(server, channel)

    def on_channel_leave(self, server, channel):
        self.window_destroy(server, channel)

    def window_create(self, server, channel):

        # Add display box
        text_box = self.new_display_box()
        self.display_boxes[(server, channel)] = text_box
        self.window_switch(server, channel)

        # Add menu item
        #TODO: Add the items in a sensible order
        menu_item = wx.MenuItem(self.channel_menu, -1, _menu_name(server,
                channel), "View Channel")
        wx.EVT_MENU(self.frame, menu_item.GetId(),
                lambda event: self.window_switch(server, channel))
        self.channel_menu.AppendItem(menu_item)

    def window_destroy(self, server, channel):

        if len(self.display_boxes) == 1:
            # Leaving the last server, show default_box
            new_server = None
            new_channel = None
        else:
            current_index = self.display_boxes.keys().index((server, channel))
            new_server, new_channel = self.display_boxes.keys()[current_index-1]

        self.window_switch(new_server, new_channel)

        del self.display_boxes[(server, channel)]

        # Remove menu item
        self.channel_menu.Remove(
            self.channel_menu.FindItem(_menu_name(server, channel))
        )

    def window_switch(self, server, channel):

        if server and channel and (server,channel) not in self.display_boxes:
            raise ValueError("Server and channel given to " \
                             "WXInterface.window_switch does not exist.")

        # Get prev_box and new_box and set window title
        if not server:
            # Switching to default box
            prev_box = self.display_boxes[(self.current_server,
                                           self.current_channel)]
            new_box = self.default_box
            self.frame.SetTitle("Pirc")

        elif self.current_server and self.current_channel:
            # Switching from channel to channel
            prev_box = self.display_boxes[(self.current_server,
                                           self.current_channel)]
            new_box = self.display_boxes[(server, channel)]
            self.frame.SetTitle(_menu_name(server, channel))

        else:
            # Switching from default box to channel
            prev_box = self.default_box
            new_box = self.display_boxes[(server, channel)]
            self.frame.SetTitle(_menu_name(server, channel))

        prev_box.Show(False)
        new_box.Show(True)
        # Replace prev_box with new_box
        self.vertical_box.Clear(False)
        self.vertical_box.Add(new_box, 1, wx.EXPAND)
        self.vertical_box.Add(self.command_box, 0, wx.EXPAND)
        self.horizontal_box.RecalcSizes()
        self.vertical_box.RecalcSizes()

        # Scroll to bottom of textbox
        new_box.SetInsertionPointEnd()

        self.current_server = server
        self.current_channel = channel

    def put_text(self, server, channel, text):

        if server:
            textbox = self.display_boxes[(server, channel)]
        else:
            textbox = self.default_box

        textbox.AppendText(text)

    def uninitialize(self):
        wx.Exit()

    def run(self):
        self.frame.Show(True)
        self.app.MainLoop()

    ################ WX Callbacks ################

    def command_box_callback(self, event):
        command_text = self.command_box.GetValue()
        self.client.run_command(command_text, self.current_server,
                                self.current_channel)
        self.command_box.Clear()

    def exit_callback(self, event):
        self.frame.Destroy()

    def focus_command_box(self, event):
        self.command_box.SetFocus()
        self.command_box.SetInsertionPointEnd()

