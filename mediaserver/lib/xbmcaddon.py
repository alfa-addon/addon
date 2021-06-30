# -*- coding: utf-8 -*-
# =======================================================================================
# librería que simula xbmcaddon para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon
# =======================================================================================
import os, sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

class Addon(object):
    def __init__(self, id):
        self.addon_name = id
        self.settings_dic = {}

        """
        Carga de configuración desde la carpeta de datos del addon o desde
        settings.xml por defecto en caso de no existir alguna clave.
        """
        from xml.etree import ElementTree

        defaultsfilepath = os.path.join(os.getcwd(), "resources", "settings.xml")
        configfilepath = os.path.join(os.path.expanduser("~"), ".{}".format(self.addon_name.split(".")[2]), "settings.xml")
        defaults = {}

        # Si existen, cargamos las preferencias del usuario
        if os.path.exists(configfilepath):
            with open(configfilepath, 'rb') as stream:
                settings = stream.read()
            root = ElementTree.fromstring(settings)
            for target in root.findall("setting"):
                self.settings_dic[target.get("id")] = target.get("value")

        # Cargamos el archivo por defecto
        with open(defaultsfilepath, 'rb') as stream:
            defaultsettings = stream.read()
        root = ElementTree.fromstring(defaultsettings)
        for category in root.findall("category"):
            for target in category.findall("setting"):
                if target.get("id"):
                    defaults[target.get("id")] = target.get("default")

        # Si no hay alguna clave en las preferencias, asignamos su valor por defecto
        for key in defaults:
            if key not in self.settings_dic:
                self.settings_dic[key] = defaults[key]

    def __str__(self):
        return 'xbmcaddon.Addon dummy object'

    def getSetting(self, setting_name):
        if self.addon_name == 'metadata.themoviedb.org':
            if setting_name == 'language':
                return 'es'
        
        elif self.addon_name == 'plugin.video.alfa':
            value = self.settings_dic.get(setting_name)

            # Devolvemos el tipo correspondiente
            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                # special case return as str
                if setting_name in ["adult_password", "adult_aux_intro_password", "adult_aux_new_password1",
                            "adult_aux_new_password2"]:
                    return value
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        pass

                    return value

    def setSetting(self, setting_name, value):
        from xml.dom import minidom

        if isinstance(value, bool):
            if value:
                value = "true"
            else:
                value = "false"
        elif isinstance(value, (int, long)):
            value = str(value)
        self.settings_dic[setting_name] = value

        # Crea un Nuevo XML vacio
        new_settings = minidom.getDOMImplementation().createDocument(None, "settings", None)
        new_settings_root = new_settings.documentElement

        for key in self.settings_dic:
            nodo = new_settings.createElement("setting")
            nodo.setAttribute("value", self.settings_dic[key])
            nodo.setAttribute("id", key)
            new_settings_root.appendChild(nodo)

        if not os.path.exists(self.getAddonInfo("Profile")):
            os.mkdir(self.getAddonInfo("Profile"))
        configfilepath = os.path.join(os.path.expanduser("~"), ".{}".format(self.addon_name.split(".")[2]), "settings.xml")

        with open(configfilepath, "wb") as fichero:
            writedata = new_settings.toprettyxml(encoding='utf-8')
            fichero.write(writedata)
        return value

    def getAddonInfo(self, key):
        def addonPath():
            return os.getcwd()

        def addonProfile():
            return os.path.join(os.path.expanduser("~"), ".{}".format(self.addon_name.split(".")[2]))
        
        functions = {"path": addonPath(),
                     "profile": addonProfile()}

        return functions.get(key.lower(), "")
