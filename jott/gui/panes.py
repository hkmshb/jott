import os
import wx
from wx import adv
from . import common, images



class FilePaneBase(wx.Panel):
    """Represents a base pane that can list file objects found at a target
    filesystem location.
    """
    bgcolor = wx.Colour(255, 255, 255)
    lbl_text = 'Pane'

    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()
        self._bind_handlers()


    def _layout_widgets(self):
        self.SetBackgroundColour(self.bgcolor)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(self, label=self.lbl_text)
        root_sizer.Add(lbl, 0, wx.TOP | wx.LEFT, 10)
        self.SetSizer(root_sizer)

    def _bind_handlers(self):
        pass


class FolderPane(FilePaneBase):
    """Represents a pane for listing folders found directly under the current
    workspace path.
    """
    bgcolor = common.COLOUR_DARK

    def __init__(self, parent, frame):
        self.frame = frame
        super().__init__(parent)

    def _layout_widgets(self):
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._font = flabel = wx.Font(common.FONTI_NSZ)
        self._font_label = self._font.Smaller().Bold()

        self.SetBackgroundColour(self.bgcolor)
        self.SetFont(self._font)

        # label
        label = wx.StaticText(self, label="System Notes")
        label.SetFont(self._font_label)
        root_sizer.Add(label, 0, wx.TOP | wx.LEFT, 10)

        # listbox
        lc_style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        self._lc_dirs = lc_dirs = wx.ListCtrl(self, style=lc_style)
        lc_dirs.SetBackgroundColour(self.bgcolor)
        lc_dirs.InsertColumn(lc_dirs.GetColumnCount(), "Directory Name", width=300)
        root_sizer.Add(lc_dirs, 1, wx.EXPAND | wx.TOP, 5)

        # new command
        btn_style = wx.BU_LEFT | wx.BORDER_NONE
        self._btn_new = btn_new = wx.Button(self, label='  New Folder', style=btn_style)
        btn_new.SetBitmap(images.folder_plus.GetBitmap())
        root_sizer.Add(btn_new, 0, wx.ALL, 10)
        self.SetSizer(root_sizer)

    def _bind_handlers(self):
        # list control
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.frame.on_dir_changed,
                  self._lc_dirs)

    def set_directory(self, dirpath):
        assert os.path.exists(dirpath), "Directory not found: %s" % dirpath

        self._current_directory = dirpath
        root, found_dirs, found_files = next(os.walk(dirpath))
        lc = self._lc_dirs

        for d in sorted(found_dirs):
            lc.InsertItem(lc.GetItemCount(), d)


class FilePane(FilePaneBase):
    """Represents a pane for listing files found directly under the currently
    selected folder in the folder pane.
    """
    bgcolor = common.COLOUR_LITE

    def __init__(self, parent, frame):
        self.frame = frame
        super().__init__(parent)

    def _layout_widgets(self):
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._font = flabel = wx.Font(common.FONTI_NSZ)
        self.SetBackgroundColour(self.bgcolor)
        self.SetFont(self._font)

        # listbox
        lc_style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        self._lc_files = lc_files = wx.ListCtrl(self, style=lc_style)
        lc_files.SetBackgroundColour(self.bgcolor)
        lc_files.InsertColumn(lc_files.GetColumnCount(), "File Name", width=300)
        root_sizer.Add(lc_files, 1, wx.EXPAND | wx.TOP, 5)
        self.SetSizer(root_sizer)

    def _bind_handlers(self):
        # list control
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.frame.on_file_changed,
                  self._lc_files)

    def show_files(self, found_files):
        lc = self._lc_files
        lc.DeleteAllItems()

        for f in sorted(found_files):
            lc.InsertItem(lc.GetItemCount(), f)


class ContentView(wx.Panel):
    """Represents a view containing a listing of files for a folder and the 
    contents of the currently selected file.
    """
    bgcolor = common.COLOUR_LITR

    def __init__(self, parent, frame):
        self.frame = frame
        super().__init__(parent)
        self._layout_widgets()

    def _layout_widgets(self):
        self.SetBackgroundColour(self.bgcolor)
        root_sizer = wx.BoxSizer(wx.VERTICAL)

        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self._pane_file = pane_file = FilePane(splitter, self.frame)
        
        self._pane_content = pane_content = wx.Window(splitter, style=wx.BORDER_NONE)
        pane_content.SetBackgroundColour(self.bgcolor)

        tx_style = wx.TE_MULTILINE | wx.TE_RICH2
        self._text_ctrl = text_ctrl = wx.TextCtrl(self._pane_content, -1, style=tx_style)
        pc_sizer = wx.BoxSizer(wx.VERTICAL)
        pc_sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 0)
        pane_content.SetSizer(pc_sizer)

        splitter.SetMinimumPaneSize(300)
        splitter.SplitVertically(pane_file, pane_content, 300)

        root_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(root_sizer)

    def set_directory(self, dirpath):
        assert os.path.exists(dirpath), "Directory not found: %s" % dirpath
        root, found_dirs, found_files = next(os.walk(dirpath))
        self._current_directory = root
        self._pane_file.show_files(found_files)

    def show_content(self, filepath):
        assert os.path.exists(filepath), "File not found: %s" % filepath
        with open(filepath, 'r') as f:
            content = ''.join(f.readlines())
            self._text_ctrl.SetValue(content)
