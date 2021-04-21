# -*- coding: utf-8 -*-#

from platformcode import config, logger
from core import filetools
from core import jsontools
import xbmc, xbmcgui
import json


info_file_path = filetools.join(config.get_runtime_path(), "resources", "help_info.json")
data_path = filetools.join(config.get_data_path(), "help_window.json")

class HelpWindow(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.title = kwargs.get('title')
        self.text = kwargs.get('text')

    def onInit(self):
        self.setFocusId(3)
        self.setProperty("title", "[B]%s[/B]" % self.title)
        self.getControl(2).setText(self.text)

    def onAction(self, action):
        if action in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_SELECT_ITEM]:
            self.close()

    def onClick(self, controlID):
        if controlID == 40000:
            self.close()


def show_info(id):

    watched = False

    with open(info_file_path, "r") as f:
        info_file = json.load(f)

    try:
        with open(data_path, "r") as f:
            watched_file = json.load(f)
        if id in watched_file:
            watched = True
    except:
        watched = False

    if id in info_file and not watched:
        title = info_file[id]["title"]
        text = info_file[id]["text"]
        window = HelpWindow('help_window.xml', config.get_runtime_path(), title=title, text=text)
        window.doModal()
        del window
        set_watched(id)


def set_watched(id):

    if filetools.exists(data_path):
        with open(data_path, "r") as f:
            data = json.load(f)
    else:
        data = dict()

    data[id] = "true"

    with open(data_path, "w") as f:
        json.dump(data, f)

