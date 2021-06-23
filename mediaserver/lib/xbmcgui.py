# -*- coding: utf-8 -*-

# librería que simula xbmcgui para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon

class Window(object):
    def __init__(self):
        pass

    def __str__(self):
        return 'xbmc dummy'

class WindowDialog(object):
    def __init__(self):
        pass

    def __str__(self):
        return 'xbmc dummy'

class WindowXMLDialog(object):
    def __init__(self):
        pass

    def __str__(self):
        return 'xbmc dummy'

class WindowXML(object):
    def __init__(self):
        pass

    def __str__(self):
        return 'xbmc dummy'

class ListItem(dict):
    def __init__(self, label="", label2="", path="", offscreen=False):
        self.label = label
        self.label2 = label2
        self.path = path
        self.offscreen = offscreen