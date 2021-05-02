import os
import xbmcgui
from quasar.addon import ADDON_PATH
from .dialog import *  # NOQA

class DialogSelect(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXML.__init__(self)
        self.items = kwargs['items']
        self.title = kwargs['title']
        self.count = 0
        self.retval = -1

    def onInit(self):
        self.getControl(32501).setLabel(self.title)
        for item in self.items:
            labels = item.split('\n')
            label1 = labels[0]
            try:
                label2 = labels[1]
            except:
                label2 = ''
            try:
                icon = labels[2]
            except:
                icon = None
            try:
                multi = labels[3] == 'multi'
            except:
                multi = False
            self.addItem(label1, label2, icon, multi)
        self.setFocusId(32503)

    def onClick(self, controlId):
        if controlId == 32500:
            # Close Button
            self.close()
        elif controlId == 32503:
            # Panel
            listControl = self.getControl(32503)
            selected = listControl.getSelectedItem()
            self.retval = int(selected.getProperty('index'))
            self.close()

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:  # NOQA
            self.close()

    def addItem(self, label1, label2, icon=None, multi=False):
        listControl = self.getControl(32503)
        item = xbmcgui.ListItem(label1, label2)
        item.setProperty('index', str(self.count))
        if multi:
            item.setArt({'icon': os.path.join(ADDON_PATH, "resources", "img", "multi-cloud.png")})
        else:
            if icon:
                item.setArt({'icon': icon})
            else:
                item.setArt({'icon': os.path.join(ADDON_PATH, "resources", "img", "cloud.png")})
        listControl.addItem(item)
        self.count += 1
