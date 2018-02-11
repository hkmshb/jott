import os
import wx
from jott.gui import JottFrame


def run_app():
    app = wx.App()
    form = JottFrame(None, size=wx.Size(1200, 800))

    # set startup workspace
    workspace_dir = os.environ.get('JOTT_WORKSPACE')
    form.set_workspace(workspace_dir)

    form.Show()
    app.MainLoop()


if __name__ == '__main__':
    run_app()
