import  wx


highlight = wx.Colour(233, 221, 175, 255)
dark = wx.Colour(240, 240, 240, 255) # wx.Colour(226, 227, 219, 250)
lite = wx.Colour(249, 249, 247, 255) # wx.Colour(229, 229, 229, 255)
litr = wx.Colour(251, 251, 249, 255) # wx.Colour(229, 229, 229, 255)


class FolderPane(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()

    def _layout_widgets(self):
        self.SetBackgroundColour(dark)
        rsizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(self, label='Folder Pane')
        rsizer.Add(lbl, 0, wx.TOP | wx.LEFT | wx.TOP, 10)
        self.SetSizer(rsizer)


class FileContentPane(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()

    def _layout_widgets(self):
        self.SetBackgroundColour(lite)
        rsizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        pane_file = wx.Window(splitter, style=wx.BORDER_NONE)
        pane_file.SetBackgroundColour(lite)

        pane_content = wx.Window(splitter, style=wx.BORDER_NONE)
        pane_content.SetBackgroundColour(litr)
        
        wx.StaticText(pane_file, label='File Pane', pos=(10, 10))
        wx.StaticText(pane_content, label='Content View', pos=(10, 10))

        splitter.SetMinimumPaneSize(300)
        splitter.SplitVertically(pane_file, pane_content, 300)

        rsizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(rsizer)


class Jott(wx.Frame):

    def __init__(self, parent, title='Jott', size=wx.DefaultSize):
        super().__init__(parent, title=title, size=size)
        self._layout_widgets()

    def _layout_widgets(self):
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        folder = FolderPane(splitter)
        content = FileContentPane(splitter)

        splitter.SetMinimumPaneSize(300)
        splitter.SplitVertically(folder, content, 300)


if __name__ == '__main__':
    app = wx.App()
    form = Jott(None, size=wx.Size(1200, 800))
    form.Show()
    app.MainLoop()
