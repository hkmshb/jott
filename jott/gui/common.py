import wx
from wx import Colour, Font


## COLORS
# background colours
BGCOLOUR_DARK = BGCOLOR_DARK = Colour(240, 240, 240, 255)
BGCOLOUR_LITE = BGCOLOR_LITE = Colour(249, 249, 247, 255)
BGCOLOUR_LITR = BGCOLOR_LITR = Colour(251, 251, 249, 255)

# text colours: filesystem pane (FSP)
FGCOLOUR_FSP_TITLE = FGCOLOR_FSP_TITLE = Colour(0, 0, 0, 150)
FGCOLOUR_FSP_ITEMS = FGCOLOR_FSP_ITEMS = Colour(0, 0, 0, 200)
HLCOLOUR_FSP_ITEMS = HLCOLOR_FLD_ITEMS = Colour(233, 221, 175, 255)


## FONTS
FONTI_LSZ = wx.FontInfo(13).Family(wx.FONTFAMILY_DEFAULT)
FONTI_NSZ = wx.FontInfo(12).Family(wx.FONTFAMILY_DEFAULT)
FONTI_MZM = wx.FontInfo(11).Family(wx.FONTFAMILY_DEFAULT)
FONTI_SSZ = wx.FontInfo(10).Family(wx.FONTFAMILY_DEFAULT)
