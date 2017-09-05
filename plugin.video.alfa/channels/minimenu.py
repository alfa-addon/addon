# -*- coding: utf-8 -*-
#------------------------------------------------------------
# XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc

from platformcode import config
from core import filetools

main = None


MAIN_MENU = {
    "news" : {"label" : "Novedades", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_news.png"), "order": 0},
    "channels" : {"label" : "Canales", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_channels.png"), "order": 1},
    "search" : {"label" : "Buscador", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_search.png"), "order": 2},
    "favorites" : {"label" : "Favoritos", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_favorites.png"), "order": 3},
    "videolibrary" : {"label" : "Videoteca", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_videolibrary.png"), "order": 4},
    "downloads" : {"label" : "Descargas", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_downloads.png"), "order": 5},
    "settings" : {"label" : "Configuración", "icon" : filetools.join(config.get_runtime_path(),"resources","media","general","default","thumb_setting_0.png"), "order": 6},
     }



class Main(xbmcgui.WindowXMLDialog):
    
    def __init__( self, *args, **kwargs ):
        self.items = []
        self.open = kwargs.get("open")

    def onInit(self):
        self.setCoordinateResolution(2)


        if self.open:
            for menuentry in MAIN_MENU.keys():
                item = xbmcgui.ListItem(MAIN_MENU[menuentry]["label"])
                item.setProperty("thumb",str(MAIN_MENU[menuentry]["icon"]))
                item.setProperty("identifier",str(menuentry))
                item.setProperty("order", str(MAIN_MENU[menuentry]["order"]))
                self.items.append(item)

            self.items.sort(key=lambda it:int(it.getProperty("order")))
            self.getControl(32500).addItems(self.items)
            self.setFocusId(32500)
            self.open = False

    def onClick(self,controlId):
        if controlId == 32500:
            identifier = self.getControl(32500).getSelectedItem().getProperty("identifier")
            if identifier == "news":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJuZXdzIg0KfQ==")')
            elif identifier == "channels":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAiZ2V0Y2hhbm5lbHR5cGVzIiwgDQogICAgImNoYW5uZWwiOiAiY2hhbm5lbHNlbGVjdG9yIg0KfQ==")')
            elif identifier == "search":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJzZWFyY2giDQp9")')
            elif identifier == "favorites":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJmYXZvcml0ZXMiDQp9")')
            elif identifier == "videolibrary":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJ2aWRlb2xpYnJhcnkiDQp9")')
            elif identifier == "downloads":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJkb3dubG9hZHMiDQp9")')
            elif identifier == "settings":
                self.close()
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJzZXR0aW5nIg0KfQ==")')



    def onAction(self,action):
        #exit
        global main
        if action.getId() == 92 or action.getId() == 10:
            main.close()
            del main
        if action.getId() == 117:
            config.open_settings()


def start(item):
    global main
    main = Main('script-shortcut-menu.xml',config.get_runtime_path(),open=True)
    main.doModal()


