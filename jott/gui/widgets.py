import os
import wx
import time
from . import common, images
from . import commands as cmds

import logging
log = logging.getLogger(__name__)


class SimpleVListBox(wx.VListBox):
    HIGHLITE_BGCOLOUR = common.HLCOLOUR_FSP_ITEMS

    def __init__(self, *args, **kw):
        kw.update({'style': wx.LB_SINGLE})
        super(SimpleVListBox, self).__init__(*args, **kw)
        self._highlite_bgcolour = self.HIGHLITE_BGCOLOUR
        self._padding_left = 20
        self._padding_right = 0
        self._padding_vert = 10
        self._inner_list = []

    @property
    def CurrentItem(self):
        index = self.GetSelection()
        if self._IsValidItemIndex(index):
            return self._inner_list[index]
        return None

    @property
    def PaddingLeft(self):
        return self._padding_left

    @PaddingLeft.setter
    def PaddingLeft(self, value):
        self._padding_left = value

    @property
    def PaddingRight(self):
        return self._padding_right

    @PaddingRight.setter
    def PaddingRight(self, value):
        self._padding_right = value

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

    def ClearItems(self):
        self._inner_list.clear()
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

    def _IsValidItemIndex(self, index):
        return (index >= 0 and index < len(self._inner_list))

    def OnDrawItem(self, dc, rect, item_idx):
        if not self._IsValidItemIndex(item_idx):
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

        if self._padding_right > 0:
            value = self._padding_right
            rect.width -= value

        flags = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        text = str(self._inner_list[item_idx])
        dc.DrawLabel(text, rect, flags)

    def OnMeasureItem(self, item_idx):
        if not self._IsValidItemIndex(item_idx):
            return 0

        text = str(self._inner_list[item_idx])
        width, height = self.GetTextExtent(text)
        return height + self._padding_vert


class FileVListBox(SimpleVListBox):
    HIGHLITE_BGCOLOUR = common.HLCOLOUR_FSP_ITEMS

    def __init__(self, *args, **kw):
        super(FileVListBox, self).__init__(*args, **kw)
        self._padding_right = 10
        self._padding_left = 10
        self._padding_vert = 20

    def OnDrawItem(self, dc, rect, item_idx):
        if not self._IsValidItemIndex(item_idx):
            return

        colour = self._highlite_bgcolour
        if self.GetSelection() != item_idx:
            colour = self.GetForegroundColour()

        font = self.GetFont()
        dc.SetFont(font.Bold())
        dc.SetTextForeground(colour)

        if self._padding_left > 0:
            value = self._padding_left
            rect.x += value
            rect.width -= value

        if self._padding_right > 0:
            value = self._padding_right
            rect.width -= value

        flags = wx.ALIGN_LEFT
        rect_height = rect.height
        file_item = self._inner_list[item_idx]

        # file name text
        text = str(file_item).upper()
        rect.height = rect_height / 2
        dc.DrawLabel(text, rect, flags | wx.ALIGN_BOTTOM)

        # last modified test
        dc.SetFont(font.Smaller().Italic())
        dc.SetTextForeground(colour.ChangeLightness(160))

        rect.Y += rect.height
        timestamp = time.asctime(time.gmtime(file_item.last_modified))
        dc.DrawLabel(timestamp, rect, flags | wx.ALIGN_TOP)

    def OnMeasureItem(self, item_idx):
        if not self._IsValidItemIndex(item_idx):
            return 0

        text = str(self._inner_list[item_idx])
        width, height = self.GetTextExtent(text)
        return (height * 2) + self._padding_vert


class FSObjectPanel(wx.Panel):
    """Represents a base pane that can list file objects found at a target
    filesystem location.
    """
    MIN_WIDTH = 180
    BGCOLOUR = common.BGCOLOUR_LITE
    FGCOLOUR_ITEMS = common.FGCOLOUR_FSP_ITEMS

    def __init__(self, *args, **kw):
        # listbox widget used to display item listings
        self._vlistbox = None

        # initialize
        super(FSObjectPanel, self).__init__(*args, **kw)
        self._layout_widgets()
        self._bind_handlers()

    def _layout_widgets(self):
        self.SetBackgroundColour(self.BGCOLOUR)
        self._root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._root_sizer)

    def _get_listbox_widget(self):
        """Returns the ListBox widget to be used for listing items within
        the panel.
        """
        raise NotImplementedError()

    def _bind_handlers(self):
        self.Bind(wx.EVT_LISTBOX, self._on_selection_changed)

    def _on_selection_changed(self, evt):
        item = self.CurrentItem
        log.debug('Selection changed. Current Item: %s' % item)
        event_args = (cmds.FSObjectPanelEventType, self.GetId(), self, item)
        event = cmds.FSObjectPanelEvent(*event_args)
        self.GetEventHandler().ProcessEvent(event)
        event.Skip()

    @property
    def CurrentItem(self):
        listbox = self._get_listbox_widget()
        return listbox.CurrentItem

    def SetItems(self, items):
        log.debug('%s.SetItems: %s' % (self.__class__.__name__, items))
        listbox = self._get_listbox_widget()
        if not items:
            listbox.ClearItems()
            return
        listbox.SetItems(items)


class DirectoryPanel(FSObjectPanel):
    """Represents a panel for listing folders in a particular folder.
    """
    BGCOLOUR = common.BGCOLOUR_DARK
    FGCOLOUR_TITLE = common.FGCOLOUR_FSP_TITLE

    def __init__(self, parent, title='System Jotts', **kw):
        super().__init__(parent, **kw)
        self.Title = title

    def _get_title(self):
        return self._lbl_title.GetLabelText()

    def _set_title(self, value):
        self._lbl_title.SetLabelText(value or '')
        self._lbl_title.Refresh()

    Title = property(_get_title, _set_title)

    def _get_listbox_widget(self):
        if self._vlistbox is None:
            listbox = SimpleVListBox(self, style=wx.BORDER_NONE)
            listbox.SetForegroundColour(self.FGCOLOUR_ITEMS)
            listbox.SetBackgroundColour(self.BGCOLOUR)
            listbox.SetItemCount(100)
            listbox.SetSelection(0)
            self._vlistbox = listbox
        return self._vlistbox

    def _layout_widgets(self):
        self.Freeze()
        super(DirectoryPanel, self)._layout_widgets()
        root_sizer = self._root_sizer
        self._font = wx.Font(common.FONTI_LSZ)
        self._font_label = self._font.Smaller().Bold()

        self.SetBackgroundColour(self.BGCOLOUR)
        self.SetFont(self._font)

        # label
        self._lbl_title = label = wx.StaticText(self, label='::[StaticText]')
        label.SetForegroundColour(self.FGCOLOUR_TITLE)
        label.SetFont(self._font_label)
        root_sizer.Add(label, 0, wx.TOP | wx.LEFT, 10)

        # listbox
        listbox = self._get_listbox_widget()
        root_sizer.Add(listbox, 1, wx.EXPAND | wx.TOP, 5)
        self.Thaw()


class FilePanel(FSObjectPanel):
    """Represents a panel for listing files in a particular directory.
    """
    MIN_WIDTH = 250

    def _get_listbox_widget(self):
        if self._vlistbox is None:
            listbox = FileVListBox(self, style=wx.BORDER_NONE)
            listbox.SetForegroundColour(self.FGCOLOUR_ITEMS)
            listbox.SetBackgroundColour(self.BGCOLOUR)
            listbox.SetItemCount(100)
            listbox.SetSelection(0)
            self._vlistbox = listbox
        return self._vlistbox

    def _layout_widgets(self):
        self.Freeze()
        super(FilePanel, self)._layout_widgets()
        root_sizer = self._root_sizer
        self._font = wx.Font(common.FONTI_LSZ)
        self.SetFont(self._font)

        # listbox
        listbox = self._get_listbox_widget()
        root_sizer.Add(listbox, 1, wx.EXPAND | wx.TOP, 0)
        self.Thaw()


class ContentBase:
    """The base class for content objects which provide a UI component
    used within a view.
    """
    def bind_to(self, parent):
        raise NotImplementedError()

    def get_content_widget(self):
        raise NotImplementedError()


class DirectoryContent(ContentBase):

    def __init__(self):
        self._current_panel = None
        self._panels = []

    @property
    def current_panel(self):
        return self._current_panel

    def bind_to(self, parent):
        assert parent and isinstance(parent, wx.Window), (
            "Parent expected and must be a Window object"
        )
        widget = self._create_layout(parent)

        # set bindings
        widget.Bind(wx.EVT_CHILD_FOCUS, self._on_panel_child_focus)
        return widget

    def _create_layout(self, parent):
        self._root_content = rcontent = wx.Panel(parent)
        self._base_content = bcontent = wx.Panel(rcontent)
        self._root_sizer = rsizer = wx.BoxSizer(wx.VERTICAL)
        self._base_sizer = bsizer = wx.BoxSizer(wx.VERTICAL)

        ## layout root controls
        rcontent.SetBackgroundColour(common.BGCOLOUR_DARK)
        rsizer.Add(bcontent, 1, wx.EXPAND)

        # create content control buttons
        btn_style = wx.BU_LEFT | wx.BORDER_NONE
        self._btn_new = btn_new =    wx.Button(rcontent, label='  New Folder', style=btn_style)
        btn_new.SetBitmap(images.folder_plus.GetBitmap())
        rsizer.Add(btn_new, 0, wx.ALL, 10)

        ## sizers
        bcontent.SetSizer(bsizer)
        rcontent.SetSizer(rsizer)
        return rcontent

    def get_content_widget(self):
        return self._root_content

    def add_directory_panel(self, title, items):
        self._base_content.Freeze()
        panel = DirectoryPanel(self._base_content, title)
        panel.SetItems(items)

        self._base_sizer.Add(panel, 1, wx.EXPAND | wx.BOTTOM, 5)
        self._base_content.Thaw()

        self._panels.append(panel)
        return panel

    def clear_panels(self):
        self.Freeze()
        for panel in self._panels:
            self._base_content.RemoveChild(panel)
            panel.Destroy()

        self._panels.clear()
        self.Thaw()

    def _on_panel_child_focus(self, event):
        log.debug('Panel Child Control Received Focus: %s' % event)
