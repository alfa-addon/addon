#from future import standard_library
#standard_library.install_aliases()
from future.builtins import map
#from future.builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.request as urllib2
else:
    import urllib2

import os
import re
import time
import xbmc
import xbmcvfs
import xbmcgui
import bjsonrpc

from bjsonrpc.handlers import BaseHandler
from quasar.addon import ADDON, ADDON_PATH
from quasar.logger import log
from quasar.config import JSONRPC_EXT_PORT, QUASARD_HOST
from quasar.osarch import PLATFORM
from quasar.util import toUtf8, notify, getLocalizedString, getLocalizedLabel, system_information
from quasar.overlay import OverlayText
from quasar.dialog_select import DialogSelect
from quasar.dialog_insert import DialogInsert

XBMC_PLAYER = xbmc.Player()

def makeMessage(*args, **kwargs):
    heading = 'Quasar'
    message = ''
    for x, value in enumerate(args):
        if x == 0:
            heading = value
            continue
        if x == 1:
            message = value
            continue
        message += '\n' + value
    for key, value in kwargs.items():
        message += '\n' + value
    return heading, message


class QuasarRPCServer(BaseHandler):
    public_methods_pattern = r'^[A-Za-z]\w+$'

    _objects = {}
    _failures = {}

    def Reset(self):
        for i in self._objects:
            try:
                self._objects[i].hide()
            except:
                pass
        log.info("Resetting RPC objects...")
        self._objects = {}

    def Refresh(self):
        return xbmc.executebuiltin("Container.Refresh")

    def InstallAddon(self, addonId):
        return xbmc.executebuiltin("InstallAddon(%s)" % addonId)

    def UpdateLocalAddons(self):
        return xbmc.executebuiltin("UpdateLocalAddons")

    def UpdateAddonRepos(self):
        return xbmc.executebuiltin("UpdateAddonRepos")

    def SystemInformation(self):
        return system_information()

    def Notify(self, header, message, image):
        return notify(getLocalizedLabel(message), header, 3000, image)

    def Keyboard(self, default="", heading="", hidden=False):
        keyboard = xbmc.Keyboard(default, getLocalizedLabel(heading), hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return keyboard.getText()

    def Dialog(self, title, message):
        dialog = xbmcgui.Dialog()
        return dialog.ok(getLocalizedLabel(title), getLocalizedLabel(message))

    def Dialog_Confirm(self, title, message):
        dialog = xbmcgui.Dialog()
        return int(dialog.yesno(getLocalizedLabel(title), getLocalizedLabel(message)))

    def Dialog_Select(self, title, items):
        dialog = xbmcgui.Dialog()
        return dialog.select(getLocalizedLabel(title), items)

    def Dialog_Select_Large(self, title, subject, items):
        title_encoded = "%s %s" % (getLocalizedLabel(title), toUtf8(subject))

        # For Kodi <= 16
        if PLATFORM['kodi'] <= 16:
            window = DialogSelect("DialogSelectLargeLegacy.xml",
                                  ADDON_PATH,
                                  "Default",
                                  title=title_encoded,
                                  items=items)
        # For Kodi >= 17
        else:
            window = DialogSelect("DialogSelectLarge.xml",
                                  ADDON_PATH,
                                  "Default",
                                  title=title_encoded,
                                  items=items)
        window.doModal()
        retval = window.retval
        del window

        return retval

    def Player_Open(self, item):
        return XBMC_PLAYER.play(item)

    def Player_GetPlayingFile(self, *args, **kwargs):
        return XBMC_PLAYER.getPlayingFile()

    def Player_IsPlaying(self, *args, **kwargs):
        return int(XBMC_PLAYER.isPlaying(*args, **kwargs))

    def Player_IsPaused(self):
        return int(xbmc.getCondVisibility("Player.Paused"))

    def Player_WatchTimes(self):
        error = ""
        watchedTime = "0"
        videoDuration = "0"
        try:
            watchedTime = str(XBMC_PLAYER.getTime())
            videoDuration = str(XBMC_PLAYER.getTotalTime())
            log.debug("Watched: %s, duration: %s" % (watchedTime, videoDuration))
        except Exception as e:
            error = "Stopped playing: %s" % repr(e)

        watchTimes = {
            "watchedTime": watchedTime,
            "videoDuration": videoDuration,
            "error": error
        }
        return watchTimes

    def Player_Seek(self, position):
        ret = ""
        try:
            XBMC_PLAYER.seekTime(position)
        except Exception as e:
            ret = repr(e)
        return ret

    def Player_SetSubtitles(self, url):
        return XBMC_PLAYER.setSubtitles(url)

    def ConvertLanguage(self, *args, **kwargs):
        return xbmc.convertLanguage(*args, **kwargs)

    def GetPlatform(self):
        return PLATFORM

    def GetAddonInfo(self):
        info = {}
        for key in ("author", "changelog", "description", "disclaimer",
                    "fanart", "icon", "id", "name", "profile", "stars",
                    "summary", "type", "version"):
            info[key] = ADDON.getAddonInfo(key)
        info['path'] = ADDON_PATH
        info['home'] = "special://home"
        info['xbmc'] = "special://xbmc"
        return info

    def AddonFailure(self, addonId):
        if ADDON.getSetting("provider_disable_failing") == u"false":
            return 0

        if addonId in self._failures:
            self._failures[addonId] += 1
        else:
            self._failures[addonId] = 1

        log.warning("Recorded failure %d for %s" % (self._failures[addonId], addonId))

        if self._failures[addonId] > int(ADDON.getSetting("provider_allowed_failures")):
            try:
                time.sleep(10)
                notify(getLocalizedString(30111))
                urllib2.urlopen("%s/provider/%s/disable" % (QUASARD_HOST, addonId))
            except:
                notify(getLocalizedString(30112))
                return 0
        return self._failures[addonId]

    def AddonCheck(self, addonId):
        if addonId in self._failures:
            return self._failures[addonId]
        return 0

    def AddonSettings(self, addonId):
        return xbmc.executebuiltin("Addon.OpenSettings(%s)" % addonId)

    def GetLanguage(self, *args, **kwargs):
        return xbmc.getLanguage(*args, **kwargs)

    def GetLocalizedString(self, *args, **kwargs):
        return ADDON.getLocalizedString(*args, **kwargs).encode('utf-8', 'ignore')

    def GetSetting(self, *args, **kwargs):
        return ADDON.getSetting(*args, **kwargs)

    def GetAllSettings(self):
        settings = []
        settingsFile = os.path.join(ADDON_PATH, "resources", "settings.xml")
        with open(settingsFile, 'r') as settingsStr:
            fileContent = settingsStr.read()
            keyType = re.findall(r".*id=\"(\w+)\".*type=\"(\w+)\"(.*option=\"(\w+)\")?", fileContent)
        for key, _type, optgroup, option in keyType:
            settings.append({
                "key": key,
                "type": _type,
                "option": option,
                "value": ADDON.getSetting(key)
            })
        return settings

    def SetSetting(self, *args, **kwargs):
        return ADDON.setSetting(*args, **kwargs)

    def GetWindowProperty(self, k):
        window = xbmcgui.Window(10000)
        return window.getProperty(k)

    def SetWindowProperty(self, k, v):
        window = xbmcgui.Window(10000)
        window.setProperty(k, v if v else "")

    def GetCurrentView(self):
        skinPath = translatePath('special://skin/')
        xml = os.path.join(skinPath, 'addon.xml')
        f = xbmcvfs.File(xml)
        read = f.read()
        f.close()
        try:
            src = re.search('defaultresolution="([^"]+)', read, re.DOTALL).group(1)
        except:
            src = re.search('<res.+?folder="([^"]+)', read, re.DOTALL).group(1)
        src = os.path.join(skinPath, src, 'MyVideoNav.xml')
        f = xbmcvfs.File(src)
        read = f.read()
        f.close()
        match = re.search('<views>([^<]+)', read, re.DOTALL)
        if match:
            views = match.group(1)
            log.info("Skin's ViewModes: %s" % views)
            for view in views.split(','):
                if xbmc.getInfoLabel('Control.GetLabel(%s)' % view):
                    return view

    def TranslatePath(self, *args, **kwargs):
        return translatePath(*args, **kwargs)

    def Log(self, *args, **kwargs):
        return xbmc.log(*args, **kwargs)

    def Dialog_CloseAll(self, *args, **kwargs):
        return xbmc.executebuiltin("Dialog.Close(all, true)")

    def DialogInsert(self, *args, **kwargs):
        if PLATFORM['kodi'] <= 16:
            window = DialogInsert("DialogInsertLegacy.xml", ADDON_PATH, "Default")
        else:
            window = DialogInsert("DialogInsert.xml", ADDON_PATH, "Default")
        window.doModal()
        retval = {"type": ("cancelled", "url", "file")[window.type], "path": window.retval}
        del window
        return retval

    ###########################################################################
    # DialogProgress
    ###########################################################################
    def DialogProgress_Create(self, *args, **kwargs):
        dialog = xbmcgui.DialogProgress()
        self._objects[id(dialog)] = dialog
        #dialog.create(*args, **kwargs)
        heading, message = makeMessage(*args, **kwargs)
        dialog.create(heading, message)
        return id(dialog)

    def DialogProgress_IsCanceled(self, hwnd, *args, **kwargs):
        #return int(self._objects[hwnd].iscanceled(*args, **kwargs))
        heading, message = makeMessage(*args, **kwargs)
        return int(self._objects[hwnd].iscanceled(heading, message))

    def DialogProgress_Update(self, hwnd, *args, **kwargs):
        #return self._objects[hwnd].update(*args, **kwargs)
        heading, message = makeMessage(*args, **kwargs)
        return self._objects[hwnd].update(heading, message)

    def DialogProgress_Close(self, hwnd, *args, **kwargs):
        dialog = self._objects.pop(hwnd)
        dialog.close()
        del dialog

    # Background DialogProgress
    def DialogProgressBG_Create(self, title, message, *args):
        dialog = xbmcgui.DialogProgressBG()
        dialogId = id(dialog)
        self._objects[dialogId] = dialog
        if args and isinstance(args[0], list):
            self._objects["%s-i18n" % dialogId] = {}
            for translation in args[0]:
                self._objects["%s-i18n" % dialogId][translation] = getLocalizedLabel(translation)
        dialog.create(title, getLocalizedLabel(message))
        return dialogId

    def DialogProgressBG_IsFinished(self, hwnd):
        return int(self._objects[hwnd].isFinished())

    def DialogProgressBG_Update(self, hwnd, percent, heading, message):
        if message.startswith("LOCALIZE"):
            message = self._objects["%s-i18n" % hwnd][message]
        return self._objects[hwnd].update(percent, heading, message)

    def DialogProgressBG_Close(self, hwnd):
        dialog = self._objects.pop(hwnd)
        if "%s-i18n" % hwnd in self._objects:
            self._objects.pop("%s-i18n" % hwnd)
        dialog.close()
        del dialog

    # Overlay status
    def OverlayStatus_Create(self):
        overlay = OverlayText()
        overlayId = id(overlay)
        self._objects[overlayId] = overlay
        return overlayId

    def OverlayStatus_Update(self, hwnd, percent, line1, line2, line3):
        text = "\n".join([line1, line2, line3])
        self._objects[hwnd].text = text

    def OverlayStatus_Show(self, hwnd):
        self._objects[hwnd].show()

    def OverlayStatus_Hide(self, hwnd):
        self._objects[hwnd].hide()

    def OverlayStatus_Close(self, hwnd):
        overlay = self._objects.pop(hwnd)
        overlay.hide()
        del overlay


def translatePath(path):
    """
    Kodi 19: xbmc.translatePath is deprecated and might be removed in future kodi versions. Please use xbmcvfs.translatePath instead.
    @param path: cadena con path special://
    @type path: str
    @rtype: str
    @return: devuelve la cadena con el path real
    """
    if PY3:
        if isinstance(path, bytes):
            path = path.decode('utf-8')
        path = xbmcvfs.translatePath(path)
        if isinstance(path, bytes):
            path = path.decode('utf-8')
    else:
        path = xbmc.translatePath(path)
    return path

def server_thread():
    try:
        bjsonrpc.bjsonrpc_options['threaded'] = True
        s = bjsonrpc.createserver(port=JSONRPC_EXT_PORT, handler_factory=QuasarRPCServer)
        log.info("quasar: starting jsonrpc service")
        s.serve()
        log.info("quasar: exiting jsonrpc service")
    except Exception:
        import traceback
        list(map(log.error, traceback.format_exc().split("\n")))
        raise
