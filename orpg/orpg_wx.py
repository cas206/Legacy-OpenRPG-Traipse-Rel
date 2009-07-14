try:
    import wxversion
    wxversion.select(["2.6", "2.7", "2.8"])
    import wx
    import wx.html
    import wx.lib.wxpTag
    import wx.grid
    import wx.media
    from wx.lib.filebrowsebutton import  *
    try:
        import wx.aui as AUI
    except:
        import orpg.tools.PyAUI as AUI
    if wx.VERSION_STRING < "2.7.2" and wx.VERSION_STRING > "2.7.0":
        AUI.AuiManager = AUI.FrameManager
        AUI.AuiManagerEvent = AUI.FrameManagerEvent
        AUI.AuiPaneInfo = AUI.PaneInfo
        AUI.AuiFloatingPane = AUI.FloatingPane
    try:
        import wx.lib.flatnotebook as FNB
        if FNB.FNB_FF2:
            pass
    except:
        import orpg.tools.FlatNotebook as FNB
    if wx.VERSION_STRING < "2.7":
        wx.Rect.Contains = lambda self, point: wx.Rect.Inside(self, point)

    WXLOADED = True
except ImportError:
    WXLOADED = False
    print "*WARNING* failed to import wxPython."
    print "Download the correct version here: http://openrpg.digitalxero.net/"
    print "If you are running the server with no gui you can ignore this message"
except Exception, e:
    WXLOADED = False
    print e
    print "\nYou do not have the correct version of wxPython installed, please"
    print "Download the correct version here: http://openrpg.digitalxero.net/"
