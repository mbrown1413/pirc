
import wx

from .base import BaseInterface

class WXInterface(BaseInterface):

    def __init__(self, client):
        self.client = client

        self.current_server = None
        self.current_channel = None

        # Maps (server, channel) to the corresponding display box
        self.display_boxes = {}

    def initialize(self):

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
        self.frame = wx.Frame(None, -1, "Pirc", size=wx.Size(500, 300))
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

        ################ Timer Setup ################
        # The timer will call self.client.handle_events() every so often.
        self.timer = wx.PyTimer(lambda: self.client.handle_events())
        self.timer.Start(2000)

        ################ Menu Setup ################
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        quit_item = wx.MenuItem(file_menu, 101, "&Quit\tCtrl+Q", "Quit PIRC")
        wx.EVT_MENU(self.frame, 101, self.exit_callback)
        file_menu.AppendItem(quit_item)
        menubar.Append(file_menu, "&File")

        # Channels menu
        self.channel_menu = wx.Menu()
        menubar.Append(self.channel_menu, "&Channels")

        self.frame.SetMenuBar(menubar)

        ################ Bind Callbacks ################

        self.frame.Bind(wx.EVT_TEXT_ENTER, self.command_box_callback)
        self.frame.Bind(wx.EVT_CLOSE, self.exit_callback)

    def new_display_box(self):
        box = wx.TextCtrl(self.panel, -1, '', style=
                wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH |
                wx.TE_AUTO_URL | wx.TE_NOHIDESEL | wx.TE_LEFT)
        box.SetDefaultStyle(self.default_style)
        return box

    def on_channel_join(self, server, channel):

        text_box = self.new_display_box()
        self.display_boxes[(server, channel)] = text_box
        self.switch_display(server, channel)

        # Add menu item
        menu_item = wx.MenuItem(self.channel_menu, -1, "%s : %s" % (server, channel), "View Channel")
        wx.EVT_MENU(self.frame, menu_item.GetId(),
                lambda event: self.switch_display(server, channel))
        self.channel_menu.AppendItem(menu_item)

    def on_channel_leave(self, server, channel):

        if len(self.display_boxes) == 1:
            # Leaving the last channel, show default_box
            new_box = self.default_box
        else:
            current_index = self.display_boxes.index((server, channel))
            new_box = self.display_boxes[current_index-1]

        self.switch_display(prev_box, new_box)

        del self.display_boxes[(server, channel)]

        # Remove menu item
        #TODO

    def switch_display(self, server, channel):

        # Get prev_box
        if self.current_server and self.current_channel:
            prev_box = self.display_boxes[(self.current_server, self.current_channel)]
        else:
            prev_box = self.default_box

        new_box = self.display_boxes[(server, channel)]

        new_box.Show(True)
        prev_box.Show(False)

        # Replace prev_box with new_box
        #self.vertical_box.Remove(prev_box)
        self.vertical_box.Clear(False)
        self.vertical_box.Add(new_box, 1, wx.EXPAND)
        self.vertical_box.Add(self.command_box, 0, wx.EXPAND)
        self.horizontal_box.RecalcSizes()
        self.vertical_box.RecalcSizes()

        self.current_server = server
        self.current_channel = channel

    def put_text(self, server, channel, text):

        if server and channel:
            textboxes = [ self.display_boxes[(server, channel)] ]
        else:
            textboxes = self.display_boxes.keys + self.default_box

        for textbox in textboxes:
            textbox.AppendText(text)

    def uninitialize(self):
        wx.Exit()

    def run(self):
        self.frame.Show(True)
        self.app.MainLoop()

    ################ WX Callbacks ################

    def command_box_callback(self, event):
        command_text = self.command_box.GetValue()
        self.client.run_command(command_text, self.current_server, self.current_channel)
        self.command_box.Clear()

    def exit_callback(self, event):
        self.frame.Destroy()
