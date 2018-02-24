
import wx
__all__ = ['EVT_FSOBJECT_PANEL', 'FSObjectPanelEvent']


## EVENTS
FSObjectPanelEventType = wx.NewEventType()
EVT_FSOBJECT_PANEL = wx.PyEventBinder(FSObjectPanelEventType, 1)


class FSObjectPanelEvent(wx.PyCommandEvent):

    def __init__(self, evt_type, id, panel, current_item):
        super(FSObjectPanelEvent, self).__init__(evt_type, id)
        self._current_item = current_item
        self._panel = panel

    @property
    def panel(self):
        return self._panel

    @property
    def current_item(self):
        return self._current_item
