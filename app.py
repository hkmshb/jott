import wx
from jott.gui import JottFrame


def run_app():
    app = wx.App()
    form = JottFrame(None, size=wx.Size(1200, 800))
    form.Show()
    app.MainLoop()


if __name__ == '__main__':
    run_app()
