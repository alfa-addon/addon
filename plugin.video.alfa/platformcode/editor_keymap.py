# -*- coding: utf-8 -*-

import xbmcgui
import xbmcaddon
from platformcode import config
from core import filetools
from threading import Timer

class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 10

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        file_name = "DialogNotification.xml" if gui_api >= (5, 11, 0) else "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, file_name, "")

    def __init__(self):
        self.key = None

    def onInit(self):
        try:
            self.getControl(401).addLabel("Presiona la tecla a usar para abrir la ventana")
            self.getControl(402).addLabel("Tienes %s segundos" % self.TIMEOUT)
        except AttributeError:
            self.getControl(401).setLabel("Presiona la tecla a usar para abrir la ventana")
            self.getControl(402).setLabel("Tienes %s segundos" % self.TIMEOUT)

        self.getControl(400).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","matchcenter.png"))

    def onAction(self, action):
        code = action.getButtonCode()
        self.key = None if code == 0 else str(code)
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


def start():
    tecla_guardada = config.get_setting("keymap_edit", "editor_keymap")
    nuevakey = KeyListener().record_key()
    if nuevakey and tecla_guardada != nuevakey:
        from core import filetools
        from platformcode import platformtools
        import xbmc
        file_xml = "special://profile/keymaps/alfa.xml"
        data = '<keymap><global><keyboard><key id="%s">' % nuevakey + 'runplugin(plugin://' \
               'plugin.video.alfa/?ew0KICAgICJhY3Rpb24iOiAic3RhcnQiLCANCiAgICAiY2hhbm5lbCI6ICJtaW5pbWVudSIsIA0KICAgICJpbmZvTGFiZWxzIjoge30NCn0=)</key></keyboard></global></keymap>'
        filetools.write(xbmc.translatePath(file_xml), data)
        platformtools.dialog_notification("Tecla guardada", "Reinicia Kodi para que se apliquen los cambios")

        from core import scrapertools
        config.set_setting("keymap_edit", nuevakey, "editor_keymap")
        file_idioma = filetools.join(config.get_runtime_path(), 'resources', 'language', 'Spanish', 'strings.xml')
        data = filetools.read(file_idioma)
        value_xml = scrapertools.find_single_match(data, '<string id="31100">([^<]+)<')
        if "tecla" in value_xml:
            data = data.replace(value_xml, 'Cambiar tecla/botón para abrir la ventana (Guardada: %s)' % nuevakey)
        elif "key" in value_xml:
            data = data.replace(value_xml, 'Change key/button to open the window (Saved: %s)' % nuevakey)
        else:
            data = data.replace(value_xml, 'Cambiamento di chiave/pulsante per aprire la finestra (Salvato: %s)' % nuevakey)
        filetools.write(file_idioma, data)

    return
