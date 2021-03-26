# -*- coding: utf-8 -*-

# librería que simula xbmc para evitar errores en módulos que lo usen en mediaserver
# y no tener que poner excepciones en el código del addon

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
    elif cond.startswith('window'):
        if cond.startswith('window.ismedia'):
            return False
    else:
        return False


def getInfoLabel(parm):
    if parm == 'Container.PluginName': return 'plugin.video.alfa'
    elif parm == 'Container.FolderName': return 'Alfa'

    return ''


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



class Monitor(object):
    class Monitor(object):
        def waitForAbort(time):
            milisec = float(time) / 1000
            time.sleep(milisec)

    def waitForAbort(time):
        milisec = float(time) / 1000
        time.sleep(milisec)


def sleep(time):
    milisec = float(time) / 1000
    time.sleep(milisec)