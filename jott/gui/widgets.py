import os
import wx
from . import common, images


class SimpleVListBox(wx.VListBox):
    HIGHLITE_BGCOLOUR = common.HLCOLOUR_FSP_ITEMS

    def __init__(self, *args, **kw):
        super(SimpleVListBox, self).__init__(*args, **kw)
        self._highlite_bgcolour = self.HIGHLITE_BGCOLOUR
        self._padding_left = 20
        self._padding_vert = 10
        self._inner_list = []

    @property
    def PaddingLeft(self):
        return self._padding_left

    @PaddingLeft.setter
    def PaddingLeft(self, value):
        self._padding_left = value

    @property
    def PaddingVertical(self):
        return self._padding_vert

    @PaddingVertical.setter
    def PaddingVertical(self, value):
        self._padding_vert = value

    def AppendItem(self, item):
        if not item:
            return
        self._inner_list.append(item)
        count = len(self._inner_list)
        if self.IsRowVisible(count):
            self.Refresh()

    def InsertItem(self, index, item):
        if index < 0 or index > len(self._inner_list):
            raise ValueError('Invalid index position for insert.')
        self._inner_list.insert(index, item)
        if self.IsRowVisible(index):
            self.Refresh()

    def SetItems(self, items):
        items = items or []
        if self._inner_list != items:
            self._inner_list = items
            self.Refresh()

    def SetItemHightliteBGColour(self, value):
        self._highlite_bgcolour = value

    def _is_valid_item_index(self, index):
        return (index >= 0 and index < len(self._inner_list))

    def OnDrawItem(self, dc, rect, item_idx):
        if not self._is_valid_item_index(item_idx):
            return

        colour = self._highlite_bgcolour
        if self.GetSelection() != item_idx:
            colour = self.GetForegroundColour()

        dc.SetFont(self.GetFont())
        dc.SetTextForeground(colour)

        if self._padding_left > 0:
            value = self._padding_left
            rect.x += value
            rect.width -= value

        dc.DrawLabel(self._inner_list[item_idx], rect,
                     wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

    def OnMeasureItem(self, item_idx):
        if not self._is_valid_item_index(item_idx):
            return 0

        text = self._inner_list[item_idx]
        width, height = self.GetTextExtent(text)
        return height + self._padding_vert


class FSObjectPanel(wx.Panel):
    """Represents a base pane that can list file objects found at a target
    filesystem location.
    """
    BGCOLOUR = wx.Colour(255, 255, 255)

    def __init__(self, parent):
        super().__init__(parent)
        self._layout_widgets()
        self._bind_handlers()

    def _layout_widgets(self):
        self.SetBackgroundColour(self.BGCOLOUR)
        self._root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._root_sizer)

    def _bind_handlers(self):
        pass


class FolderPanel(FSObjectPanel):
    """Represents a pane for listing folders found directly under the current
    Jottbook directory path.
    """
    MIN_WIDTH = 150
    BGCOLOUR = common.BGCOLOUR_DARK
    FLD_TCOLOUR = common.FGCOLOUR_FSP_TITLE
    FLD_ICOLOUR = common.FGCOLOUR_FSP_ITEMS

    def __init__(self, parent, title='System Jotts'):
        super().__init__(parent)
        self.Title = title

    def _get_title(self):
        return self._lbl_title.GetLabelText()

    def _set_title(self, value):
        self._lbl_title.SetLabelText(value or '')
        self._lbl_title.Refresh()

    Title = property(_get_title, _set_title)

    def _layout_widgets(self):
        self.Freeze()
        super(FolderPane, self)._layout_widgets()
        root_sizer = self._root_sizer
        self._font = flabel = wx.Font(common.FONTI_LSZ)
        self._font_label = self._font.Smaller().Bold()

        self.SetBackgroundColour(self.BGCOLOUR)
        self.SetFont(self._font)

        # label
        self._lbl_title = label = wx.StaticText(self, label='::[StaticText]')
        label.SetForegroundColour(self.FLD_TCOLOUR)
        label.SetFont(self._font_label)
        root_sizer.Add(label, 0, wx.TOP | wx.LEFT, 10)

        # listbox
        self._vlistbox = listbox = SimpleVListBox(self, style=wx.BORDER_NONE)
        listbox.SetForegroundColour(self.FLD_ICOLOUR)
        listbox.SetBackgroundColour(self.BGCOLOUR)
        listbox.SetItems(['Item #1', 'Item #2'])
        listbox.SetItemCount(100)
        listbox.SetSelection(0)

        root_sizer.Add(listbox, 1, wx.EXPAND | wx.TOP, 5)
        self.SetSizer(root_sizer)
        self.Thaw()
