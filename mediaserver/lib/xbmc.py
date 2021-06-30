# -*- coding: utf-8 -*-

# librería que simula xbmc para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon
import os

warning_xbmcvfs = "WARNING: xbmc.{} is deprecated and might be removed in future kodi versions. Please use xbmcvfs.{} instead."

def getCondVisibility(cond):
    cond = cond.lower()
    import sys
    if cond.startswith('system'):
        if cond.startswith('system.platform'):
            is_platform = False
            platform = sys.platform
            if 'linux' in platform and cond.endswith('linux'):
                is_platform =  True
            elif 'darwin' in platform and cond.endswith('osx'):
                is_platform =  True
            elif 'win32' in platform and cond.endswith('windows'):
                is_platform =  True
            return is_platform
    elif cond.startswith('window'):
        if cond.startswith('window.ismedia'):
            return False
    else:
        return False

def getInfoLabel(param):
    param = str(param)
    if param.startswith("Container"):
        if param == 'Container.PluginName': return 'plugin.video.alfa'
        elif param == 'Container.FolderName': return 'Alfa'
    return ''

def sleep(time):
    milisec = float(time) / 1000
    time.sleep(milisec)


# xbmcvfs functions (deprecated in Kodi 19 Matrix)

def makeLegalFilename(path):
    print(warning_xbmcvfs.format("makeLegalFilename", "makeLegalFilename"))
    from lib import xbmcvfs
    return xbmcvfs.makeLegalFilename(path)

def translatePath(path):
    print(warning_xbmcvfs.format("translatePath", "translatePath"))
    from lib import xbmcvfs
    return xbmcvfs.translatePath(path)

def validatePath(path):
    print(warning_xbmcvfs.format("validatePath", "validatePath"))
    from lib import xbmcvfs
    return xbmcvfs.validatePath(path)

class Monitor(object):
    class Monitor(object):
        def waitForAbort(time):
            milisec = float(time) / 1000
            time.sleep(milisec)

    def waitForAbort(time):
        milisec = float(time) / 1000
        time.sleep(milisec)

class Player(object):
    def __init__(self):
        pass

    def __str__(self):
        return 'xbmc dummy'

    def play(item=None, listitem=None, windowed=False, startpos=0):
        return True

    def stop():
        return True

    def pause():
        return True

    def playnext():
        return True

    def isPlaying(*args, **kwargs):
        return False

    def setSubtitles(subtitleFile):
        return True
