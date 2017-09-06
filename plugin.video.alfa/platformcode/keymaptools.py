# -*- coding: utf-8 -*-

from threading import Timer

import xbmc
import xbmcaddon
import xbmcgui
from core import filetools
from platformcode import config


class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 10

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        if gui_api >= (5, 11, 0):
            filenname = "DialogNotification.xml"
        else:
            filenname = "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, filenname, "")

    def __init__(self):
        self.key = None

    def onInit(self):
        try:
            self.getControl(401).addLabel("Presiona la tecla a usar para abrir la ventana")
            self.getControl(402).addLabel("Tienes %s segundos" % self.TIMEOUT)
        except AttributeError:
            self.getControl(401).setLabel("Presiona la tecla a usar para abrir la ventana")
            self.getControl(402).setLabel("Tienes %s segundos" % self.TIMEOUT)

    def onAction(self, action):
        code = action.getButtonCode()
        if code == 0:
            self.key = None
        else:
            self.key = str(code)
        self.close()

    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        return key


def set_key():
    saved_key = config.get_setting("shortcut_key")
    new_key = KeyListener().record_key()

    if new_key and saved_key != new_key:
        from core import filetools
        from platformcode import platformtools
        import xbmc
        file_xml = "special://profile/keymaps/alfa.xml"
        data = '<keymap><global><keyboard><key id="%s">' % new_key + 'runplugin(plugin://' \
                                                                     'plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAia2V5bWFwIiwNCiAgICAib3BlbiI6IHRydWUNCn0=)</key></keyboard></global></keymap>'
        filetools.write(xbmc.translatePath(file_xml), data)
        platformtools.dialog_notification("Tecla guardada", "Reinicia Kodi para que se apliquen los cambios")

        config.set_setting("shortcut_key", new_key)
        # file_idioma = filetools.join(config.get_runtime_path(), 'resources', 'language', 'Spanish', 'strings.xml')
        # data = filetools.read(file_idioma)
        # value_xml = scrapertools.find_single_match(data, '<string id="31100">([^<]+)<')
        # if "tecla" in value_xml:
        #     data = data.replace(value_xml, 'Cambiar tecla/botón para abrir la ventana (Guardada: %s)' % new_key)
        # elif "key" in value_xml:
        #     data = data.replace(value_xml, 'Change key/button to open the window (Saved: %s)' % new_key)
        # else:
        #     data = data.replace(value_xml,
        #                         'Cambiamento di chiave/pulsante per aprire la finestra (Salvato: %s)' % new_key)
        # filetools.write(file_idioma, data)

    return


MAIN_MENU = {
    "news": {"label": "Novedades",
             "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                    "thumb_news.png"), "order": 0},
    "channels": {"label": "Canales",
                 "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                        "thumb_channels.png"), "order": 1},
    "search": {"label": "Buscador",
               "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                      "thumb_search.png"), "order": 2},
    "favorites": {"label": "Favoritos",
                  "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                         "thumb_favorites.png"), "order": 3},
    "videolibrary": {"label": "Videoteca",
                     "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                            "thumb_videolibrary.png"), "order": 4},
    "downloads": {"label": "Descargas",
                  "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                         "thumb_downloads.png"), "order": 5},
    "settings": {"label": "Configuración",
                 "icon": filetools.join(config.get_runtime_path(), "resources", "media", "general", "default",
                                        "thumb_setting_0.png"), "order": 6},
}


class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []
        self.open = kwargs.get("open")

    def onInit(self):
        self.setCoordinateResolution(2)

        if self.open:
            for menuentry in MAIN_MENU.keys():
                item = xbmcgui.ListItem(MAIN_MENU[menuentry]["label"])
                item.setProperty("thumb", str(MAIN_MENU[menuentry]["icon"]))
                item.setProperty("identifier", str(menuentry))
                item.setProperty("order", str(MAIN_MENU[menuentry]["order"]))
                self.items.append(item)

            self.items.sort(key=lambda it: it.getProperty("order"))
            self.getControl(32500).addItems(self.items)
            self.setFocusId(32500)
            self.open = False

    def onClick(self, control_id):
        if control_id == 32500:
            identifier = self.getControl(32500).getSelectedItem().getProperty("identifier")
            if identifier == "news":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJuZXdzIg0KfQ==")')
            elif identifier == "channels":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAiZ2V0Y2hhbm5lbHR5cGVzIiwgDQogICAgImNoYW5uZWwiOiAiY2hhbm5lbHNlbGVjdG9yIg0KfQ==")')
            elif identifier == "search":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJzZWFyY2giDQp9")')
            elif identifier == "favorites":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJmYXZvcml0ZXMiDQp9")')
            elif identifier == "videolibrary":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJ2aWRlb2xpYnJhcnkiDQp9")')
            elif identifier == "downloads":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJkb3dubG9hZHMiDQp9")')
            elif identifier == "settings":
                self.close()
                xbmc.executebuiltin(
                    'ActivateWindow(10025, "plugin://plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAibWFpbmxpc3QiLCANCiAgICAiY2hhbm5lbCI6ICJzZXR0aW5nIg0KfQ==")')

            config.set_setting("shortcut_flag", "")

    def onAction(self, action):
        # exit
        if action.getId() in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            # main.close()
            self.close()
            config.set_setting("shortcut_flag", "")

        if action.getId() == xbmcgui.ACTION_CONTEXT_MENU:
            config.open_settings()


def open_shortcut_menu():
    if config.get_setting("shortcut_flag") != "open":
        main = Main('ShortCutMenu.xml', config.get_runtime_path(), open=True)
        config.set_setting("shortcut_flag", "open")
        main.doModal()
        del main
