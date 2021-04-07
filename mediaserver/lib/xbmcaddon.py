# -*- coding: utf-8 -*-

# librería que simula xbmcaddon para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon

class Addon(object):
    def __init__(self, name):
        self.addon_name = name

    def __str__(self):
        return 'xbmc dummy'

    def getSetting(self, setting_name):
        if self.addon_name == 'metadata.themoviedb.org':
            if setting_name == 'language':
                return 'es'