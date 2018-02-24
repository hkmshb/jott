import os
import  wx
from . import panes, images


wx.ToolTip.Enable(True)


class JottFrame(wx.Frame):
    TB_FLAGS = (wx.TB_HORIZONTAL | wx.TB_FLAT)


    def __init__(self, parent, title='Jott', size=wx.DefaultSize):
        # vars
        self._workspace_dir = None
        self._current_dir = None

        super().__init__(parent, title=title, size=size)
        self._root_sizer = wx.BoxSizer(wx.VERTICAL)
        self._layout_widgets()


    def _layout_widgets(self):
        self.Freeze()

        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self._pane_folder = folder = panes.FolderPane(splitter, self)
        self._pane_content = content = panes.ContentView(splitter, self)

        splitter.SetMinimumPaneSize(300)
        splitter.SplitVertically(folder, content, 300)

        # create toolbar
        self._create_toolbar()

        # add objects to sizer
        self._root_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(self._root_sizer)
        self.Thaw()

    def _create_toolbar(self):
        self.toolbar = tb = self.CreateToolBar(self.TB_FLAGS)
        self.toolbar.SetToolBitmapSize((16,15))

        btn_styles = wx.BU_NOTEXT | wx.BU_EXACTFIT
        btn_size = (20, 17) # (36, 17)

        def add_btn(_id, tooltip_text, img):
            button = wx.Button(tb, size=btn_size, style=btn_styles)
            button.SetToolTip(wx.ToolTip(tooltip_text))
            button.SetBitmap(img)
            tb.AddControl(button)

        def add_tgl(_id, tooltip_text, img):
            button = wx.ToggleButton(tb, size=btn_size)
            button.SetToolTip(wx.ToolTip(tooltip_text))
            button.SetBitmap(img)
            tb.AddControl(button)

        def add_search(_id, tooltip_text, img):
            self._search = wx.SearchCtrl(tb, size=(210,-1), style=wx.TE_PROCESS_ENTER)
            self._search.ShowSearchButton(True)
            self._search.ShowCancelButton(True)
            tb.AddControl(self._search)

        # self.SetToolBar(tb)
        tb.AddSeparator()
        add_btn(101, "Hide Pane", images.app_sidebar.GetBitmap())
        add_tgl(102, "Browse attachments", images.paper_clip.GetBitmap())
        add_btn(103, "Delete", images.bin_full.GetBitmap())
        add_btn(104, "Create a note", images.report_pencil.GetBitmap())
        tb.AddSeparator()
        add_btn(105, "Add or remove password lock", images.lock_warning.GetBitmap())
        add_btn(106, "Add a table", images.table_plus.GetBitmap())
        add_btn(107, "Make a checklist", images.ui_check_box.GetBitmap())
        add_btn(108, "Choose a style to apply to text", images.edit_size.GetBitmap())
        tb.AddStretchableSpace()
        add_btn(109, "Account", images.user_medium.GetBitmap())
        add_btn(110, "Share", images.upload_cloud.GetBitmap())
        add_search(111, "Search", None)
        tb.Realize()

    def set_workspace(self, dirpath):
        if not os.path.isdir(dirpath):
            print('Directory not found: %s' % dirpath)
            return

        self._workspace_dir = dirpath
        self._pane_folder.set_directory(dirpath)

    def on_dir_changed(self, event):
        fullpath = os.path.join(self._workspace_dir, event.GetLabel())
        if not os.path.isdir(fullpath):
            return 

        self._current_dir = fullpath
        self._pane_content.set_directory(fullpath)

    def on_file_changed(self, event):
        fullpath = os.path.join(self._current_dir, event.GetLabel())
        if not os.path.isfile(fullpath):
            return

        self._pane_content.show_content(fullpath)