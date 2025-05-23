from __future__ import with_statement
import wx, sys, os #just .sep maybe
from manifest import manifest
import shutil

from orpg.orpgCore import component
from orpg.dirpath import dir_struct
from orpg.tools.orpg_log import logger, crash
from upmana.validate import validate
from orpg.dirpath import dir_struct
from mercurial import ui, hg, commands, repo, revlog, cmdutil, util

class Term2Win(object):
    # A stdout redirector.  Allows the messages from Mercurial to be seen in the Install Window
    def write(self, text):
        self.closed = sys.__stdout__.closed
        self.flush = sys.__stdout__.flush
        statbar.SetStatusText(text.replace('\n', ''))
        sys.__stdout__.write(text)

class Updater(wx.Panel):
    def __init__(self, parent, component):
        wx.Panel.__init__(self, parent)
        ### Status Bar ###
        #statbar.SetStatusText('Select a Package and Update')
        #statbar.SetStatusText('New Status Bar')

        self.timer = wx.Timer(self, 1)
        self.count = 0

        ### Update Manager
        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')
        self.parent = parent
        self.SetBackgroundColour(wx.WHITE)
        self.sizer = wx.GridBagSizer(hgap=1, vgap=1)
        self.changelog = wx.TextCtrl(self, wx.ID_ANY, size=(300, -1), 
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.filelist = wx.TextCtrl(self, wx.ID_ANY, size=(275, 300), 
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.buttons = {}
        self.buttons['progress_bar'] = wx.Gauge(self, wx.ID_ANY, 100)
        self.buttons['auto_text'] = wx.StaticText(self, wx.ID_ANY, "Auto Update")
        self.buttons['auto_check'] = wx.CheckBox(self, wx.ID_ANY)
        self.buttons['no_text'] = wx.StaticText(self, wx.ID_ANY, "No Update")
        self.buttons['no_check'] = wx.CheckBox(self, wx.ID_ANY)
        self.buttons['advanced'] = wx.Button(self, wx.ID_ANY, "Package Select")
        self.buttons['update'] = wx.Button(self, wx.ID_ANY, "Update Now")
        self.buttons['finish'] = wx.Button(self, wx.ID_ANY, "Finish")

        self.sizer.Add(self.changelog, (0,0), span=(5,1), flag=wx.EXPAND)
        self.sizer.Add(self.filelist, (0,1), span=(1,3), flag=wx.EXPAND)

        self.sizer.Add(self.buttons['progress_bar'], (1,1), span=(1,3), flag=wx.EXPAND)
        self.sizer.Add(self.buttons['auto_text'], (2,1))
        self.sizer.Add(self.buttons['auto_check'], (2,2), flag=wx.EXPAND)
        self.sizer.Add(self.buttons['no_text'], (3,1))
        self.sizer.Add(self.buttons['no_check'], (3,2), flag=wx.EXPAND)
        self.sizer.Add(self.buttons['advanced'], (2,3), flag=wx.EXPAND)
        self.sizer.Add(self.buttons['update'], (3,3), flag=wx.EXPAND)
        self.sizer.Add(self.buttons['finish'], (4,3), flag=wx.EXPAND)
        self.buttons['progress_bar'].SetValue(100)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.get_package

        self.current = self.repo.dirstate.branch()
        self.BranchInfo(self.current)

        if manifest.GetString("updatemana", "no_update", "") == 'on': self.buttons['no_check'].SetValue(True)
        else: self.buttons['no_check'].SetValue(False)
        if manifest.GetString("updatemana", "auto_update", "") == 'on': self.buttons['auto_check'].SetValue(True)
        else: self.buttons['auto_check'].SetValue(False)

        ## Event Handlers
        self.Bind(wx.EVT_BUTTON, self.Update, self.buttons['update'])
        self.Bind(wx.EVT_BUTTON, self.Finish, self.buttons['finish'])
        self.Bind(wx.EVT_BUTTON, self.ChooseBranch, self.buttons['advanced'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleAutoUpdate, self.buttons['auto_check'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleNoUpdate, self.buttons['no_check'])
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

    def OnTimer(self, event):
        statbar.SetStatusText('Checking For Updates')
        self.count = self.count + 1
        self.buttons['progress_bar'].SetValue(self.count)
        if self.count == 100:
            self.timer.Stop()
            statbar.SetStatusText('No Updates Available')

    def UpdateCheck(self):
        self.timer.Start(100)
        self.count = 3
        self.buttons['progress_bar'].SetValue(3)
        try:
            doUpdate = commands.incoming(self.ui, self.repo, 
                        manifest.GetString('default', 'repo', ''), 
                        force=True, bundle=False)
            if doUpdate:
                statbar.SetStatusText('No Updates Available')
                self.buttons['progress_bar'].SetValue(100)
                self.timer.Stop()
            else:
                statbar.SetStatusText('Refresh Repo For Updated Source')
                self.buttons['progress_bar'].SetValue(100)
                self.timer.Stop()
        except:
            statbar.SetStatusText('No Connection Found')
            self.buttons['progress_bar'].SetValue(100)
            self.timer.Stop()


    def ToggleAutoUpdate(self, event):
        if self.buttons['auto_check'].GetValue() == True:
            if self.buttons['no_check'].GetValue() == True: 
                self.buttons['no_check'].SetValue(False)
                manifest.SetString("updatemana", "no_update", "off")
            manifest.SetString("updatemana", "auto_update", "on")
        else: manifest.SetString("updatemana", "auto_update", "off")

    def ToggleNoUpdate(self, event):
        if self.buttons['no_check'].GetValue() == True:
            if self.buttons['auto_check'].GetValue() == True: 
                self.buttons['auto_check'].SetValue(False)
                manifest.SetString("updatemana", "auto_update", "off")
            manifest.SetString("updatemana", "no_update", "on")
        else: manifest.SetString("updatemana", "no_update", "off")

    def Update(self, evt=None):
        top_folder = dir_struct['home'].split(str(os.sep))
        top_folder.pop(); top_folder.pop(); top_folder = str(os.sep).join(top_folder)+os.sep

        with open(top_folder+'location.py', 'rb') as f: old_location = f.read()
        ## This new location file update allows for a more portable way to start Traipse. It's aimed at Linux users.
        new_location = """import sys
import os

dyn_dir = 'System'
_home = sys.path[0]
_userbase_dir = _home + os.sep + dyn_dir
sys.path.append(_userbase_dir)
try: os.chdir(_userbase_dir)
except: print 'Failed to find ' + _userbase_dir + '\\nHopefuly you are running setup.py which would make this error normal.'"""

        if new_location != old_location:
            with open(top_folder+'location.py', 'w') as f: f.write(new_location)

        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')
        filename = 'ignorelist.txt'
        self.filename = dir_struct["home"] + 'upmana' + os.sep + filename
        component.get('validate').config_file(filename, "default_ignorelist.txt")
        self.mana = self.LoadDoc()
        temp = dir_struct["home"] + 'upmana' + os.sep + 'tmp' + os.sep
        for ignore in self.ignorelist:
            if len(ignore.split('/')) > 1:
                gets = 0; dir1 = ''
                while gets != len(ignore.split('/'))-1:
                    dir1 += ignore.split('/')[gets] + os.sep
                    gets += 1
                os.makedirs(temp+dir1)
            shutil.copy(ignore, temp + dir1 + ignore.split('/')[len(ignore.split('/')) - 1])
        hg.clean(self.repo, self.current)
        for ignore in self.ignorelist:
            shutil.copyfile(temp + ignore.split('/')[len(ignore.split('/')) - 1], ignore)
            os.remove(temp + ignore.split('/')[len(ignore.split('/')) - 1])
            if len(ignore.split('/')) > 1:
                gets = 0; dir1 = ''
                while gets != len(ignore.split('/'))-1:
                    dir1 += ignore.split('/')[gets] + os.sep
                    gets += 1
                os.removedirs(temp+dir1)

    def LoadDoc(self):
        manifest = open(self.filename)
        self.ignorelist = []
        ignore = manifest.readlines()
        for i in ignore: self.ignorelist.append(str(i[:len(i)-1]))
        manifest.close()

    def Finish(self, evt=None):
        component.get('upmana-win').OnClose(None)

    def ChooseBranch(self, evt=None):
        dlg = wx.Dialog(self, wx.ID_ANY, "Package Selector", style=wx.DEFAULT_DIALOG_STYLE)
        if wx.Platform == '__WXMSW__': icon = wx.Icon(dir_struct["icon"]+'d20.ico', wx.BITMAP_TYPE_ICO)
        else: icon = wx.Icon(dir_struct["icon"]+"d20.xpm", wx.BITMAP_TYPE_XPM )
        dlg.SetIcon(icon)

        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')

        dlgsizer = wx.GridBagSizer(hgap=1, vgap=1)
        Yes = wx.Button( dlg, wx.ID_OK, "Ok" )
        Yes.SetDefault()
        rgroup = wx.RadioButton(dlg, wx.ID_ANY, "group_start", style=wx.RB_GROUP)
        rgroup.Hide()

        self.get_packages()
        if self.package_list == None: return
        types = self.package_list
        row=0; col=0
        self.current = self.repo.dirstate.branch()
        self.package_type = self.current
        self.btnlist = {}; self.btn = {}
        self.id = 1

        for t in types:
            self.btnName = str(t)
            self.btn[self.id] = wx.RadioButton(dlg, wx.ID_ANY, str(t), name=self.btnName)
            if self.btnName == self.current: self.btn[self.id].SetValue(True); self.current_id = self.id
            self.btnlist[self.id] = self.btnName
            dlgsizer.Add(self.btn[self.id], (row, col))
            col += 1; self.id += 1
            if col == 3: row += 1; col = 0

        dlgsizer.Add(Yes, (row+1,col/2))
        dlgsizer.AddGrowableCol(0)
        dlgsizer.AddGrowableRow(0)
        dlg.SetAutoLayout( True )
        dlg.SetSizer( dlgsizer )
        dlgsizer.Fit( dlg )
        dlg.Centre()
        dlg.Bind(wx.EVT_RADIOBUTTON, self.PackageSet)
        if dlg.ShowModal(): dlg.Destroy()

    def PackageSet(self, event):
        for btn in self.btn:
            if self.btn[btn].GetValue() == True:
                if self.btnlist[btn] == 'pious-paladin':
                    try: from PyQt4 import QtCore
                    except:
                        error = "'Pious Paladin' requires PyQt 4.6. For stability you will not be able to update."
                        dlg = wx.MessageDialog(None, error, 'Failed PyQt Test', wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        self.btn[self.current_id].SetValue(True)
                        self.current = self.btnlist[self.current_id]
                else: self.current = self.btnlist[btn]

        branches = self.repo.branchtags()
        heads = dict.fromkeys(self.repo.heads(), 1)
        l = [((n in heads), self.repo.changelog.rev(n), n, t) for t, n in branches.items()]

        if self.current != type:
            heads = dict.fromkeys(self.repo.heads(), self.repo.branchtags())
            branches = dict.copy(self.repo.branchtags())
            self.BranchInfo(self.current)

    def BranchInfo(self, branch):
        cs = self.repo.changectx( self.current ).changeset()
        self.changelog.SetValue('')
        changelog = cs[4]
        self.changelog.AppendText(changelog + '\n')
        self.filelist.SetValue('')
        self.filelist.AppendText("Currently selected branch: " + branch + "\n\nAuthor: "+cs[1]+"\n\n")
        self.filelist.AppendText("Files Modified (in update): \n")
        for f in cs[3]: self.filelist.AppendText(f+"\n")

    def get_packages(self, type=None):
        #Fixed and ready for Test. Can be cleaner
        self.package_list = []
        b = self.repo.branchtags()
        heads = dict.fromkeys(self.repo.heads(), 1) #The code below looks superfluous but there is good info inside
        l = [((n in heads), self.repo.changelog.rev(n), n, t) for t, n in b.items()]
        l.sort()
        l.reverse()
        for ishead, r, n, t in l: self.package_list.append(t)

    def get_package(self):
        self.get_packages()
        if self.package_list == None: return None
        return None

class Repos(wx.Panel):
    def __init__(self, parent, openrpg):
        wx.Panel.__init__(self, parent)
        ### Status Bar ###
        #statbar.SetStatusText('Add, Delete, or Refresh your source Tracs')
        statbar.SetStatusText('New Status Bar')
        ### Update Manager
        self.ui = ui.ui()
        self.r = hg.repository(self.ui, ".")
        self.c = self.r.changectx('tip')

        #mainpanel = self
        self.openrpg = openrpg
        self.buttons = {}
        self.texts = {}

        ## Section Sizers (with frame edges and text captions)
        self.box_sizers = {}
        self.box_sizers["newbutton"] = wx.StaticBox(self, -1)

        ## Layout Sizers
        self.sizers = {}
        self.sizers["main"] = wx.GridBagSizer(hgap=2, vgap=2)
        self.sizers["button"] = wx.GridBagSizer(hgap=2, vgap=2)

        #Button Layout
        self.sizers["newbutton"] = wx.StaticBoxSizer(self.box_sizers["newbutton"], wx.VERTICAL)
        self.sizers["newrepo_layout"] = wx.FlexGridSizer(rows=1, cols=2, hgap=2, vgap=5)
        empty = wx.StaticText(self, -1, "")
        reponame = wx.StaticText(self, -1, "Name:")
        self.texts["reponame"] = wx.TextCtrl(self, -1, '')
        self.buttons['addrepo'] = wx.Button(self, wx.ID_NEW)

        ##Build Button
        self.sizers["newrepo_layout"].Add(self.buttons['addrepo'], -1, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizers["newrepo_layout"].Add(empty, -1)
        self.sizers["newrepo_layout"].Add(reponame, -1, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizers["newrepo_layout"].Add(self.texts["reponame"], -1, wx.EXPAND)
        self.sizers["newrepo_layout"].AddGrowableCol(1)
        self.sizers["newbutton"].Add(self.sizers["newrepo_layout"], -1, wx.EXPAND)

        #Repo List Panel
        self.repopanel = wx.ScrolledWindow(self)
        self.repopanel.SetScrollbars(20,20,55,40)
        self.repopanel.Scroll(50,10)
        self.box_sizers["repolist"] = wx.StaticBox(self.repopanel, -1, "Current Repo List")
        self.sizers["repolist"] = wx.StaticBoxSizer(self.box_sizers["repolist"], wx.VERTICAL)
        self.sizers["repo"] = wx.GridBagSizer(hgap=2, vgap=2)
        self.sizers["repolist_layout"] = wx.FlexGridSizer(rows=1, cols=1, hgap=2, vgap=5)

        self.NewRepoList(None)
        self.BuildRepoList(None)

        self.sizers["repolist_layout"].AddGrowableCol(0)
        self.sizers["repolist"].Add(self.sizers["repolist_layout"], -1, wx.EXPAND)
        self.sizers["repo"].Add(self.sizers["repolist"], (0,0), flag=wx.EXPAND)
        self.sizers["repo"].AddGrowableCol(0)
        self.sizers['repo'].AddGrowableRow(0)
        self.sizers['repo'].AddGrowableRow(1)
        self.repopanel.SetSizer(self.sizers['repo'])
        self.repopanel.SetAutoLayout(True)

        #Build Main Sizer
        self.sizers["main"].Add(self.sizers["newbutton"], (0,0), flag=wx.EXPAND)
        self.sizers["main"].Add(self.repopanel, (1,0), flag=wx.EXPAND)
        self.sizers["main"].AddGrowableCol(0)
        self.sizers["main"].AddGrowableCol(1)
        self.sizers["main"].AddGrowableRow(1)
        self.SetSizer(self.sizers["main"])
        self.SetAutoLayout(True)
        #self.Fit()
        self.Bind(wx.EVT_BUTTON, self.AddRepo, self.buttons['addrepo'])

    def NewRepoList(self, event):
        self.id = -1
        self.box = {}; self.box_name= {}; self.main = {}; self.container = {}; self.layout = {}
        self.name = {}; self.url = {}; self.url_list = {}; self.pull = {}; self.uri = {}; self.delete = {}
        self.defaultcheck = {}; self.default = {}; self.repotrac = {}
        self.pull_list = {}; self.delete_list = {}; self.defchecklist = {}; self.repolist = []

    def BuildRepoList(self, event):
        repolist = manifest.PluginChildren('updaterepo')
        appendlist = []
        for repo in repolist:
            if repo not in self.repolist: appendlist.append(repo)
        self.repolist = repolist

        for repo in appendlist:
            self.id += 1
            #Build Constructs
            self.box[self.id] = wx.StaticBox(self.repopanel, -1, str(repo))
            self.main[self.id] = wx.GridBagSizer(hgap=2, vgap=2)
            self.container[self.id] = wx.StaticBoxSizer(self.box[self.id], wx.VERTICAL)
            self.layout[self.id] = wx.FlexGridSizer(rows=1, cols=4, hgap=2, vgap=5)
            self.name[self.id] = wx.StaticText(self.repopanel, -1, 'URL')
            self.uri[self.id] = manifest.GetString('updaterepo', repo, '')
            #except: self.uri[self.id] = ''
            self.url[self.id] = wx.TextCtrl(self.repopanel, -1, self.uri[self.id])
            self.pull[self.id] = wx.Button(self.repopanel, wx.ID_REFRESH)
            self.delete[self.id] = wx.Button(self.repopanel, wx.ID_DELETE)
            self.delete_list[self.delete[self.id]] = self.id
            self.defaultcheck[self.id] = wx.CheckBox(self.repopanel, -1)
            self.default[self.id] = wx.StaticText(self.repopanel, -1, 'Default')
            #Build Retraceables
            self.box_name[self.id] = str(repo)
            self.pull_list[self.pull[self.id]] = self.id
            self.defchecklist[self.defaultcheck[self.id]] = self.id
            #Build Layout
            self.layout[self.id].Add(self.name[self.id], 
                                    -1, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
            self.layout[self.id].Add(self.url[self.id], 
                                    -1, wx.EXPAND)
            self.layout[self.id].Add(self.pull[self.id], 
                                    -1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
            self.layout[self.id].Add(self.delete[self.id], -1, wx.EXPAND)
            self.layout[self.id].Add(self.defaultcheck[self.id], 
                                    -1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
            self.layout[self.id].Add(self.default[self.id], -1, wx.EXPAND)
            self.layout[self.id].AddGrowableCol(1)
            self.container[self.id].Add(self.layout[self.id], -1, wx.EXPAND)
            #Button Events
            self.Bind(wx.EVT_BUTTON, self.RefreshRepo, self.pull[self.id])
            self.Bind(wx.EVT_BUTTON, self.DelRepo, self.delete[self.id])
            self.Bind(wx.EVT_CHECKBOX, self.SetDefault, self.defaultcheck[self.id])
            self.sizers["repolist_layout"].Insert(0, self.container[self.id], -1, wx.EXPAND)
            self.sizers['repolist_layout'].Layout()
        self.Layout()

        #Set Default Repo Button
        capture = manifest.GetString('default', 'repo', '')
        if capture != '':
            for caught in self.uri:
                if capture == self.uri[caught]: self.id = caught; pass
                else: continue
            self.defaultcheck[self.id].SetValue(True)

    def AddRepo(self, event):
        repo = self.texts['reponame'].GetValue(); repo = repo.replace(' ', '_'); repo = 'repo-' + repo
        manifest.SetString('updaterepo', repo, '')
        self.BuildRepoList(None)

    def DelRepo(self, event):
        self.id = self.delete_list[event.GetEventObject()]
        self.sizers["repolist_layout"].Hide(self.container[self.id])
        manifest.DelString('updaterepo', self.box_name[self.id])
        try: del self.box_name[self.id]
        except: pass
        self.sizers['repolist_layout'].Layout()
        self.repolist = manifest.PluginChildren('updaterepo')

    def RefreshRepo(self, event):
        self.id = self.pull_list[event.GetEventObject()]
        manifest.SetString('updaterepo', str(self.box_name[self.id]), self.url[self.id].GetValue())
        try: commands.pull(self.ui, self.r, self.url[self.id].GetValue(), rev='', update=False, force=True)
        except: pass

    def SetDefault(self, event):
        self.id = self.defchecklist[event.GetEventObject()]
        manifest.SetString('default', 'repo', self.uri[self.id])
        for all in self.defaultcheck:
            self.defaultcheck[all].SetValue(False)
        self.defaultcheck[self.id].SetValue(True)

class Manifest(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        ### Status Bar ###
        #statbar.SetStatusText('Create an Ignore List')
        statbar.SetStatusText('New Status Bar')
        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')
        self.manifestlist = []
        self.manifestlist = self.c.manifest().keys()
        for mana in self.manifestlist: mana = os.sep + 'orpg' + os.sep + mana
        self.manifestlist.sort()
        self.SetBackgroundColour(wx.WHITE)
        self.sizer = wx.GridBagSizer(hgap=1, vgap=1)
        self.manifestlog = wx.CheckListBox( self, -1, wx.DefaultPosition, wx.DefaultSize, 
                                            self.manifestlist, wx.LC_REPORT|wx.SUNKEN_BORDER|wx.EXPAND|wx.LC_HRULES)
        filename = 'ignorelist.txt'
        self.filename = dir_struct["home"] + 'upmana' + os.sep + filename
        component.get('validate').config_file(filename, "default_ignorelist.txt")
        self.mana = self.LoadDoc()
        self.manifestlog.Bind(wx.EVT_CHECKLISTBOX, self.GetChecked)
        self.sizer.Add(self.manifestlog, (0,0), flag=wx.EXPAND)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

    def GetChecked(self, event):
        self.mana = []
        for manifest in self.manifestlog.GetChecked(): self.mana.append(self.manifestlist[manifest])
        self.SaveDoc()

    def SaveDoc(self):
        f = open(self.filename, "w")
        for mana in self.mana: f.write(mana+'\n')
        f.close()

    def LoadDoc(self):
        ignore = open(self.filename)
        ignorelist = []
        for i in ignore: ignorelist.append(str(i [:len(i)-1]))
        for i in ignorelist: #Adds previously ignored files to manifestlistlog if they are not in changesets.
            if self.c.manifest().has_key(i): continue
            else: self.manifestlist.append(i); self.manifestlist.sort()
        self.manifestlog = wx.CheckListBox( self, -1, wx.DefaultPosition, wx.DefaultSize, self.manifestlist, 
            wx.LC_REPORT|wx.SUNKEN_BORDER|wx.EXPAND|wx.LC_HRULES)
        self.manifestlog.SetCheckedStrings(ignorelist)
        manifest = ignore.readlines()
        ignore.close()

class Control(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        ### Status Bar ###
        #statbar.SetStatusText('Advanced Controls & Rollback')
        statbar.SetStatusText('New Status Bar')
        ### Control Panel
        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')
        self.parent = parent
        #logger.debug("Enter updaterFrame") #Need to set logging level

        self.get_packages()
        self.SetBackgroundColour(wx.WHITE)
        self.sizer = wx.GridBagSizer(hgap=1, vgap=1)
        self.buttons = {}

        ## Changelog / File List
        changelogcp = wx.Panel(self)
        self.changelogcp = wx.GridBagSizer(hgap=1, vgap=1)
        self.changelog = wx.TextCtrl(changelogcp, wx.ID_ANY, size=wx.DefaultSize, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.filelist = wx.TextCtrl(changelogcp, wx.ID_ANY, size=wx.DefaultSize, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.changelogcp.Add(self.changelog, (0,0), flag=wx.EXPAND)
        self.changelogcp.Add(self.filelist, (1,0), flag=wx.EXPAND)
        changelogcp.SetSizer(self.changelogcp)
        self.changelogcp.AddGrowableCol(0)
        self.changelogcp.AddGrowableRow(0)
        self.changelogcp.AddGrowableRow(1)
        changelogcp.SetAutoLayout(True)

        ## Branches / Revisions
        branchcp = wx.Panel(self)
        self.current = self.repo.dirstate.branch()
        self.branchcp = wx.GridBagSizer(hgap=1, vgap=1)
        self.branches = wx.Choice(branchcp, wx.ID_ANY, choices=self.package_list)
        self.branches.SetSelection(self.package_list.index(self.current))
        self.branch_txt = wx.StaticText(branchcp, wx.ID_ANY, "Branches")
        self.branchcp.Add(self.branches, (0,0))
        self.branchcp.Add(self.branch_txt, (0,1), flag=wx.ALIGN_CENTER_VERTICAL)
        branchcp.SetSizer(self.branchcp)
        branchcp.SetAutoLayout(True)

        revlistcp = wx.Panel(self)
        self.revlistcp = wx.GridBagSizer(hgap=2, vgap=2)
        self.revlist = wx.ListCtrl(revlistcp, -1, wx.DefaultPosition, size=wx.DefaultSize, 
                                    style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES)
        self.revlist.InsertColumn(0, 'Revs')
        self.revlist.InsertColumn(1, 'Changeset')
        self.revlist.SetColumnWidth(0, -1)
        self.revlist.SetColumnWidth(1, -1)
        self.revlist.Refresh()
        self.revlistcp.Add(self.revlist, (0,0), flag=wx.EXPAND)
        revlistcp.SetSizer(self.revlistcp)
        self.revlistcp.AddGrowableCol(0)
        self.revlistcp.AddGrowableRow(0)
        self.revlistcp.AddGrowableRow(1)
        revlistcp.SetAutoLayout(True)

        ## Control Panel
        cp = wx.Panel(self)
        self.cp = wx.GridBagSizer(hgap=1, vgap=1)
        self.buttons['update'] = wx.Button(cp, wx.ID_ANY, "Revision Update")
        self.buttons['delete'] = wx.Button(cp, wx.ID_ANY, "Delete Branch")
        self.cp.Add(self.buttons['update'], (0,0))
        self.cp.Add(self.buttons['delete'], (0,1))
        cp.SetSizer(self.cp)
        cp.SetAutoLayout(True)

        self.sizer.Add(changelogcp, (0,0), span=(3,1), flag=wx.EXPAND)
        self.sizer.Add(branchcp, (0,1), span=(1,1))
        self.sizer.Add(revlistcp, (2,1), span=(1,1), flag=wx.EXPAND)
        self.sizer.Add(cp, (1,1), span=(1,1))

        self.buttons['delete'].Disable()
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(2)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

        self.currev = self.repo.changelog.rev(self.repo.branchtags()[self.current])
        self.RevInfo(self.currev)
        self.revlist.Select(self.revlist.FindItem(0, str(self.currev), 1))
        self.BranchInfo(self.current)
        self.Bind(wx.EVT_CHOICE, self.PackageSet)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.RevSet)
        self.Bind(wx.EVT_BUTTON, self.RevUpdate, self.buttons['update'])


    def PackageSet(self, event):
        self.current = self.branches.GetStringSelection()
        branches = self.repo.branchtags()
        heads = dict.fromkeys(self.repo.heads(), 1)
        l = [((n in heads), self.repo.changelog.rev(n), n, t) for t, n in branches.items()]
        if self.current != type:
            heads = dict.fromkeys(self.repo.heads(), self.repo.branchtags())
            branches = dict.copy(self.repo.branchtags())
            self.BranchInfo(self.current)
            self.RevInfo(self.current)

    def RevSet(self, event):
        self.currev = self.revlist.GetItemText( self.revlist.GetFirstSelected() )
        i = event.GetIndex()
        self.revlist.Select(i, True)
        self.revlist.Focus(i)
        self.BranchInfo(self.current)
        if self.currev != self.revlist.GetItemText( self.revlist.GetFirstSelected() ):
            self.RevInfo(self.currev)

    def RevInfo(self, rev):
        self.revlist.DeleteAllItems()
        self.revlist_a = []; self.revlist_b = {}
        for heads in self.repo.changelog.reachable(self.repo.branchtags()[self.current]):
            self.revlist_a.append(str(self.repo.changelog.rev(heads)))
            self.revlist_b[str(self.repo.changelog.rev(heads))] = str(self.repo.changectx(heads))
        self.revlist_a.sort()
        for i in self.revlist_a:
            self.revlist.InsertStringItem(0, str(i), 0 )
            self.revlist.SetStringItem(0, 1, self.revlist_b[i])
            self.revlist.SetColumnWidth(0, -1)
            self.revlist.SetColumnWidth(1, -1)
        self.revlist.Refresh()
        self.BranchInfo(self.current)

    def BranchInfo(self, branch):
        rs = self.repo.changectx( self.currev ).changeset()
        self.changelog.SetValue('')
        changelog = rs[4]
        self.changelog.AppendText(changelog + '\n')
        self.filelist.SetValue('')
        self.filelist.AppendText("Currently selected branch: " + branch + "\n\nAuthor: "+rs[1]+"\n\n")
        self.filelist.AppendText("Files Modified (in update): \n")
        for f in rs[3]: self.filelist.AppendText(f+"\n")

    def DelBranch(self, event):
        pass

    def RevUpdate(self, event):
        dlg = wx.MessageDialog(None, 'Revision Updates are recommended for Developers only.\n\nAre you sure to preform a Revision Update?\n\nNewer builds tend to have less bugs while older revisions may no longer function properly.', 'Expert Feature', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            filename = 'ignorelist.txt'
            self.filename = dir_struct["home"] + 'upmana' + os.sep + filename
            component.get('validate').config_file(filename, "default_ignorelist.txt")
            self.mana = self.LoadDoc()
            temp = dir_struct["home"] + 'upmana' + os.sep + 'tmp' + os.sep
            for ignore in self.ignorelist:
                shutil.copy(ignore, temp + ignore.split('/')[len(ignore.split('/')) - 1])
            hg.clean(self.repo, self.currev)
            for ignore in self.ignorelist:
                shutil.copyfile(temp + ignore.split('/')[len(ignore.split('/')) - 1], ignore)
                os.remove(temp + ignore.split('/')[len(ignore.split('/')) - 1])
        else:
            dlg.Destroy(); pass

    def LoadDoc(self):
        manifest = open(self.filename)
        self.ignorelist = []
        ignore = manifest.readlines()
        for i in ignore: self.ignorelist.append(str(i[:len(i)-1]))
        manifest.close()

    def get_packages(self, type=None):
        #Can be cleaner
        self.package_list = []
        b = self.repo.branchtags()
        heads = dict.fromkeys(self.repo.heads(), 1) #The code below looks superfluous but there is good info inside
        l = [((n in heads), self.repo.changelog.rev(n), n, t) for t, n in b.items()]
        l.sort()
        l.reverse()
        for ishead, r, n, t in l: self.package_list.append(t)

    def get_package(self):
        self.get_packages()
        if self.package_list == None: return None
        return None

class Help(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.help = wx.TextCtrl(self, wx.ID_ANY, size=(-1, -1), 
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.help, 1, wx.EXPAND)
        self.build_help()
        self.SetSizer(sizer)
        self.Layout()

    def build_help(self):
        help = """'Traipse' OpenRPG Update Manager Help:
The Traipse Update Manager can be confusing at first glance. There is alot involved in the new addition so it is easy to by pass the finer details. This small page will help a new user understand how to use the new Update Manager to it's full capability.\n\n"""
        self.help.AppendText(help)
        help = """The Different Tabs: There are 5 different tabs available to users, and each tab has a different purpose. These five tabs are: Updater, Repos, Manifest, Control and Help.
---

The Updater Tab:
The Updater tab is divided into three sections. The left section shows a description of the your current or selected version.  The right top section shows the files that have been updated in your current or selected version.  Underneath is a selection of buttons and check boxes.

Package Select: 
When you press this button a small window pops up showing you the available packages to update too. You can select a package and the Updater's detail sections will reflect the change.

Update Now: 
Press this button when you want to update to the selected package

Auto Update: 
Check this if want to update when you start the software. You need to have a default Repository checked in the Repo tab.

No Update: 
Check this if you do not want to see the Update Manager when you start the software.
---\n\n"""
        self.help.AppendText(help)
        help = """The Repos Tab:
The Repos tab has two parts to it. The top most part is a section is where you name and create repositories.  The second part shows you a list of all your available repositories.

What is a repostiory? 
1: a place, room, or container where something is deposited or stored (Merriam-Webster). A repository, or repo for short, is a place to hold source code so others can download it.

Creating new Repos:
Creating a new repos is really easy. First you need to give your repo a name, any name will work, then press the New button. You will see that your named repo shows up in your list immediately.

You will then need to connect the named repo to a URL so you can download source code.  Enter a URL (http://hg.assembla.com/traipse) into the new entry and press the Refresh button. This downloads the new source code to your computer only. Refreshing a repo does not update your software.

Default: 
You can set any repo as your default repository. This is the repo the software will update from if you Auto Update.
---\n\n"""
        self.help.AppendText(help)
        help = """The Manifest Tab:
The Manifest Tab is really easy to understand, it's just named differently. The manifest shows a list of all the files that are being tracked by your current package. Checking files in the list will place them into a list that prevents these files from being changed when you update to a new package.

The manifest can cause problems with compatibility if the newer source does not understand the unchanged files, so it would be smart to test out a new package in a different folder.
---\n\n"""
        self.help.AppendText(help)
        help = """The Control Tab:
The control tab is recommended for developers only. The control tab contains the two details elements from the Updater tab and a new section that contains all of the revisions for your selected package.

You can select any of the available packages from the drop down and the list of revisions will change. You can also select any of the revisions in the list and the details on the left side will change to reflect the details of that revision.

You are also allowed to update to any of the selected revisions. Older revisions often times contain bugs and newer methods of coding, so revision updates commonly cause problems with software.

What is the Control Tab for?
The control tab is for developers who want to see how the source code has changed from revision to revision. When a user downloads the software they also download all past revisions made to that software. This tab allows users to roll back if a problem has been created with new source, or for developers they can watch the software evolve.
---"""
        self.help.AppendText(help)

class updaterFrame(wx.Frame):
    def __init__(self, parent, title, openrpg, manifest, main):

        wx.Frame.__init__(self, None, wx.ID_ANY, title, size=(600,500), style=wx.DEFAULT_FRAME_STYLE)
        if wx.Platform == '__WXMSW__': icon = wx.Icon(dir_struct["icon"]+'d20.ico', wx.BITMAP_TYPE_ICO)
        else: icon = wx.Icon(dir_struct["icon"]+"d20.xpm", wx.BITMAP_TYPE_XPM )

        self.SetIcon(icon)
        self.main = main
        ####### Panel Stuff ######
        p = wx.Panel(self)
        nb = wx.Notebook(p)

        global statbar
        statbar = self.CreateStatusBar()
        sys.stdout = Term2Win()
        self.Centre()

        # create the page windows as children of the notebook
        self.page1 = Updater(nb, openrpg)
        page2 = Repos(nb, openrpg)
        page3 = Manifest(nb)
        page4 = Control(nb)
        page5 = Help(nb)

        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(self.page1, "Updater")
        nb.AddPage(page2, "Repos")
        nb.AddPage(page3, "Manifest")
        nb.AddPage(page4, "Control")
        nb.AddPage(page5, 'Help')

        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)
        p.Layout()
        self.Refresh()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        component.add('upmana-win', self)

    def OnClose(self, event):
        if self.main == False: self.Destroy()
        if self.main == True: self.Hide()

class updateApp(wx.App):
    def OnInit(self):
        self.main = False; self.autoUpdate = False; self.noUpdate = False
        logger._set_log_to_console(False)
        logger.note("Updater Start")
        component.add('validate', validate)
        self.updater = updaterFrame(self, "OpenRPG Update Manager 1.2", 
                                component, manifest, self.main)
        if manifest.GetString("updatemana", "auto_update", "") == 'on' and self.main == False:
            self.AutoUpdate(); self.OnExit(); self.autoUpdate = True
        else: pass
        if manifest.GetString('updatemana', 'no_update', '') == 'on' and self.main == False: 
            self.OnExit(); self.noUpdate = True
        else: pass
        if not (self.autoUpdate or self.noUpdate):
            try:
                self.updater.Show()
                self.updater.Fit()
                if not self.main: self.updater.page1.UpdateCheck()
            except: pass
        return True

    def AutoUpdate(self):
        self.ui = ui.ui()
        self.repo = hg.repository(self.ui, ".")
        self.c = self.repo.changectx('tip')
        self.current = self.repo.dirstate.branch()

        capture = manifest.GetString('default', 'repo', '')
        if capture != '':
            try: commands.pull(self.ui, self.repo, capture, rev='', update=False, force=True)
            except:
                wx.MessageBox('No Connection Found.  Skipping Auto Update!', 'Info')
                return
            filename = 'ignorelist.txt'
            self.filename = dir_struct["home"] + 'upmana' + os.sep + filename
            component.get('validate').config_file(filename, "default_ignorelist.txt")
            self.mana = self.LoadDoc(); ignored = []
            temp = dir_struct["home"] + 'upmana' + os.sep + 'tmp' + os.sep
            for ignore in self.ignorelist:
                if len(ignore.split('/')) > 1:
                    gets = 0; dir1 = ''
                    while gets != len(ignore.split('/'))-1:
                        dir1 += ignore.split('/')[gets] + os.sep
                        gets += 1
                    os.makedirs(temp+dir1)
                ignoredfile = temp + dir1 + ignore.split('/')[len(ignore.split('/')) - 1]
                ignored.append(ignoredfile)
                shutil.copy(ignore, ignoredfile)
            hg.clean(self.repo, self.current)
            for ignore in self.ignorelist:
                shutil.copyfile(ignored.index(ignore), ignore)
                os.remove(ignored.index(ignore))
                if len(ignore.split('/')) > 1:
                    gets = 0; dir1 = ''
                    while gets != len(ignore.split('/'))-1:
                        dir1 += ignore.split('/')[gets] + os.sep
                        gets += 1
                    os.removedirs(temp+dir1)
        else: wx.MessageBox('Default Repo Not Found.  Skipping Auto Update!', 'Info')

    def LoadDoc(self):
        manifest = open(self.filename)
        self.ignorelist = []
        ignore = manifest.readlines()
        for i in ignore: self.ignorelist.append(str(i[:len(i)-1]))
        manifest.close()

    def OnExit(self):
        imported = ['manifest', 'orpg.dirpath', 'orpg.orpgCore', 'orpg.orpg_version', 
                    'orpg.tools.orpg_log', 'orpg.tools.orpg_log', 'orpg.orpg_xml', 'orpg.dirpath', 
                    'orpg.dirpath', 'upmana.validate', 'mercurial.ui', 'mercurial.hg', 
                    'mercurial.commands', 'mercurial.repo', 'mercurial.revlog', 'mercurial.cmdutil', 'shutil']
        for name in imported:
            if name in sys.modules: del sys.modules[name]

        try: self.updater.Destroy()
        except: pass
