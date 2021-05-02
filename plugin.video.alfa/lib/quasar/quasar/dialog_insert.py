import xbmcgui
from .dialog import *  # NOQA

class DialogInsert(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXML.__init__(self)

    def onInit(self):
        self.setOption1()
        self.retval = ""

    def onClick(self, controlId):
        if controlId == 32500:
            # Close Button
            self.cancelled()
        elif controlId == 32501:
            # Radio Button 1
            self.setOption1()
        elif controlId == 32502:
            # Radio Button 2
            self.setOption2()
        elif controlId == 32508:
            # OK button
            self.OK()
        elif controlId == 32505:
            # Option 1 url button
            self.setURL()
        elif controlId == 32507:
            # Option 2 path button
            self.setPath()

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:  # NOQA
            self.cancelled()

    def setOption1(self):
        self.getControl(32501).setSelected(True)  # Radio Button 1
        self.getControl(32502).setSelected(False)  # Radio Button 2
        self.type = 1

    def getURL(self):
        # return self.getControl(32505).getText()
        return self.getControl(32505).getLabel()

    def setOption2(self):
        self.getControl(32501).setSelected(False)  # Radio Button 1
        self.getControl(32502).setSelected(True)  # Radio Button 2
        self.type = 2

    def setURL(self):
        url = xbmcgui.Dialog().input("Quasar")
        if url != "":
            self.getControl(32505).setLabel(url)

    def setPath(self):
        fn = xbmcgui.Dialog().browse(1, "Quasar", "files", ".torrent").decode('utf-8')
        if fn != "":
            self.getControl(32507).setLabel(fn)

    def getPath(self):
        return self.getControl(32507).getLabel()

    def cancelled(self):
        self.type = 0
        self.close()

    def OK(self):
        if self.type == 1:
            # Option 1 text input
            self.retval = self.getURL()
        elif self.type == 2:
            # Option 2 text input
            self.retval = self.getPath()
        self.close()
