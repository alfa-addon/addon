# -*- coding: utf-8 -*-

# librería que simula xbmc para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon

def getInfoLabel(parm):
    if parm == 'Container.PluginName': return 'plugin.video.alfa'
    elif parm == 'Container.FolderName': return 'Alfa'

    return ''

