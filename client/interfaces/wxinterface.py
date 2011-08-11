
import wx

from .base import BaseInterface

class WXInterface(BaseInterface):

    def initialize(self):

        ################ Layout Setup ################
        # The layout has the following hierarchy:
        #   frame
        #     |
        #     -- horizontal_box
        #          |
        #          -- vertical_box
        #               |
        #               -- text_box
        #               |
        #               -- command_box
        #
        # The horizontal_box is present to make the contents fit the width of
        # the window.  If there is a better way to do this, please suggest
        # something.

        self.app = wx.App()
        self.frame = wx.Frame(None, -1, "Pirc", size=wx.Size(500, 300))
        self.frame.SetPosition(wx.Point(100, 100))
        panel = wx.Panel(self.frame, -1)

        self.default_style = wx.TextAttr("black", "white", wx.Font(8, wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL), False)

        self.text_box = wx.TextCtrl(panel, -1, '', style=
            wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_AUTO_URL |
            wx.TE_NOHIDESEL | wx.TE_LEFT)
        self.command_box = wx.TextCtrl(panel, -1, '', style=wx.TE_PROCESS_ENTER)
        self.text_box.SetDefaultStyle(self.default_style)
        self.frame.Bind(wx.EVT_TEXT_ENTER, self.command_box_callback)

        vertical_box = wx.BoxSizer(wx.VERTICAL)
        vertical_box.Add(self.text_box, 1, wx.EXPAND)
        vertical_box.Add(self.command_box, 0, wx.EXPAND)

        horizontal_box = wx.BoxSizer(wx.HORIZONTAL)
        horizontal_box.Add(vertical_box, 1, wx.EXPAND)

        panel.SetSizer(horizontal_box)

        ################ Timer Setup ################
        # Set up timer
        # The timer will call self.client.handle_events() every so often.
        self.timer = wx.PyTimer(lambda: self.client.handle_events())
        self.timer.Start(2000)

        ################ Menu Setup ################
        '''
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        quit_item = wx.MenuItem(file_menu, 105, "&Quit\tCtrl+Q", "Quit PIRC")
        file_menu.AppendItem(quit_item)

        menubar.Append(file_menu, "&File")

        self.frame.SetMenuBar(menubar)
        '''

    def put_text(self, text):
        self.text_box.AppendText(text)

    def command_box_callback(self, event):
        command_text = self.command_box.GetValue()
        self.client.run_command(command_text)
        self.command_box.Clear()

    def uninitialize(self):
        wx.Exit()

    def run(self):
        self.frame.Show(True)
        self.app.MainLoop()

