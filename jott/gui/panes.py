import wx
from . import common



class FilePaneBase(wx.Panel):
    """Represents a base pane that can list file objects found at a target
    filesystem location.
    """
    bgcolor = wx.Colour(255, 255, 255)
    lbl_text = 'Pane'

    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()

    def _layout_widgets(self):
        self.SetBackgroundColour(self.bgcolor)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(self, label=self.lbl_text)
        root_sizer.Add(lbl, 0, wx.TOP | wx.LEFT, 10)
        self.SetSizer(root_sizer)


class FolderPane(FilePaneBase):
    """Represents a pane for listing folders found directly under the current
    workspace path.
    """
    bgcolor = common.COLOUR_DARK
    lbl_text = 'Folder Pane'


class FilePane(FilePaneBase):
    """Represents a pane for listing files found directly under the currently
    selected folder in the folder pane.
    """
    bgcolor = common.COLOUR_LITE
    lbl_text = 'File Pane'


class ContentView(wx.Panel):
    """Represents a view containing a listing of files for a folder and the 
    contents of the currently selected file.
    """
    bgcolor = common.COLOUR_LITR

    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()

    def _layout_widgets(self):
        self.SetBackgroundColour(self.bgcolor)
        root_sizer = wx.BoxSizer(wx.VERTICAL)

        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        pane_file = FilePane(splitter)

        pane_content = wx.Window(splitter, style=wx.BORDER_NONE)
        pane_content.SetBackgroundColour(self.bgcolor)

        splitter.SetMinimumPaneSize(300)
        splitter.SplitVertically(pane_file, pane_content, 300)

        root_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(root_sizer)
