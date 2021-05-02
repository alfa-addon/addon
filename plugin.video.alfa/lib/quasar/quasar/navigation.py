#from future import standard_library
#standard_library.install_aliases()
from future.builtins import map
#from future.builtins import str
from future.builtins import range
from future.builtins import object

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.request as urllib2
    import urllib.parse as urlparse
    import urllib.response as urllib
else:
    import urllib2
    import urlparse
    import urllib

import os
import socket

import xbmc
import xbmcgui
import xbmcplugin
from quasar.logger import log
from quasar.config import QUASARD_HOST
from quasar.addon import ADDON, ADDON_ID, ADDON_PATH
from quasar.util import notify, getLocalizedString, getLocalizedLabel, system_information

import json


HANDLE = int(sys.argv[1])


class InfoLabels(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        return dict.get(self, key.lower(), "")

    def __setitem__(self, key, val):
        dict.__setitem__(self, key.lower(), val)

    def update(self, *args, **kwargs):
        for k, v in list(dict(*args, **kwargs).items()):
            self[k] = v


class closing(object):
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        return self.thing

    def __exit__(self, *exc_info):
        self.thing.close()


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, headers["Location"])
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


def getInfoLabels():
    id_list = [int(s) for s in sys.argv[0].split("/") if s.isdigit()]
    tmdb_id = id_list[0] if id_list else None
                                   
    if not tmdb_id:
        parsed_url = urlparse.urlparse(sys.argv[0] + sys.argv[2])
        query = urlparse.parse_qs(parsed_url.query)
        log.debug("Parsed URL: %s, Query: %s", repr(parsed_url), repr(query))
        if 'tmdb' in query and 'type' in query and query['type'][0] == 'movie':
            tmdb_id = query['tmdb'][0]
            url = "%s/movie/%s/infolabels" % (QUASARD_HOST, tmdb_id)
        elif 'show' in query:
            tmdb_id = query['show'][0]
            if 'season' in query and 'episode' in query:
                url = "%s/show/%s/season/%s/episode/%s/infolabels" % (QUASARD_HOST, tmdb_id, query['season'][0], query['episode'][0])
            else:
                url = "%s/show/%s/infolabels" % (QUASARD_HOST, tmdb_id)
        else:
            url = "%s/infolabels" % (QUASARD_HOST)
    elif 'movie' in sys.argv[0]:
        url = "%s/movie/%s/infolabels" % (QUASARD_HOST, tmdb_id)
    elif ('episode' in sys.argv[0] or 'show' in sys.argv[0]) and len(id_list) > 2:
        url = "%s/show/%s/season/%s/episode/%s/infolabels" % (QUASARD_HOST, tmdb_id, id_list[1], id_list[2])
    elif 'show' in sys.argv[0] and len(id_list) == 2:
        url = "%s/show/%s/season/%s/episode/%s/infolabels" % (QUASARD_HOST, tmdb_id, id_list[1], 1)
    else:
        url = "%s/infolabels" % (QUASARD_HOST)

    log.debug("Resolving TMDB item by calling %s for %s" % (url, repr(sys.argv)))

    try:
        with closing(urllib2.urlopen(url)) as response:
            resolved = json.loads(response.read(), parse_int=str)
            if not resolved:
                return {}

            if 'info' in resolved and resolved['info']:
                resolved.update(resolved['info'])

            if 'art' in resolved and resolved['art']:
                resolved['artbanner'] = ''
                for k, v in list(resolved['art'].items()):
                    resolved['art' + k] = v

            if 'info' in resolved:
                del resolved['info']
            if 'art' in resolved:
                del resolved['art']
            if 'stream_info' in resolved:
                del resolved['stream_info']

            if 'dbtype' not in resolved:
                resolved['dbtype'] = 'video'
            if 'mediatype' not in resolved or resolved['mediatype'] == '':
                resolved['Mediatype'] = resolved['dbtype']

            return resolved
    except:
        log.debug("Could not resolve TMDB item: %s" % tmdb_id)
        return {}


def _json(url):
    with closing(urllib2.urlopen(url)) as response:
        if response.code >= 300 and response.code <= 307:
            # Pause currently playing Quasar file to avoid doubling requests
            if xbmc.Player().isPlaying() and ADDON_ID in xbmc.Player().getPlayingFile():
                xbmc.Player().pause()
            _infoLabels = InfoLabels(getInfoLabels())
            
            item = xbmcgui.ListItem(
                    path=response.geturl(),
                    label=_infoLabels["label"],
                    label2=_infoLabels["label2"])

            item.setArt({
                "thumb": _infoLabels["artthumb"],
                "poster": _infoLabels["artposter"],
                "tvshowposter": _infoLabels["arttvshowposter"],
                "banner": _infoLabels["artbanner"],
                "fanart": _infoLabels["artfanart"],
                "clearart": _infoLabels["artclearart"],
                "clearlogo": _infoLabels["artclearlogo"],
                "landscape": _infoLabels["artlandscape"],
                "icon": _infoLabels["articon"]
            })

            item.setInfo(type='Video', infoLabels=_infoLabels)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)
            return

        payload = response.read()

        try:
            if payload:
                return json.loads(payload)
        except:
            raise Exception(payload)


def run(url_suffix=""):
    if not os.path.exists(os.path.join(ADDON_PATH, ".firstrun")):
        notify(getLocalizedString(30101))
        system_information()
        return

    donatePath = os.path.join(ADDON_PATH, ".donate")
    if not os.path.exists(donatePath):
        with open(donatePath, "w"):
            os.utime(donatePath, None)
        dialog = xbmcgui.Dialog()
        dialog.ok("Quasar", getLocalizedString(30141))

    socket.setdefaulttimeout(int(ADDON.getSetting("buffer_timeout")))
    urllib2.install_opener(urllib2.build_opener(NoRedirectHandler()))

    # Pause currently playing Quasar file to avoid doubling requests
    if xbmc.Player().isPlaying() and ADDON_ID in xbmc.Player().getPlayingFile():
        xbmc.Player().pause()

    url = sys.argv[0].replace("plugin://%s" % ADDON_ID, QUASARD_HOST + url_suffix) + sys.argv[2]
    log.debug("Requesting %s from %s" % (url, repr(sys.argv)))

    try:
        data = _json(url)
    except urllib2.URLError as e:
        if 'Connection refused' in e.reason:
            notify(getLocalizedString(30116), time=7000)
        else:
            import traceback
            list(map(log.error, traceback.format_exc().split("\n")))
            notify(e.reason, time=7000)
        return
    except Exception as e:
        import traceback
        list(map(log.error, traceback.format_exc().split("\n")))
        try:
            msg = unicode(e)
        except:
            try:
                msg = str(e)
            except:
                msg = repr(e)
        notify(getLocalizedLabel(msg), time=7000)
        return

    if not data:
        return

    if data["content_type"]:
        content_type = data["content_type"]
        if data["content_type"].startswith("menus"):
            content_type = data["content_type"].split("_")[1]

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        if content_type != "tvshows":
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        else:
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.setContent(HANDLE, content_type)

    listitems = list(range(len(data["items"])))
    for i, item in enumerate(data["items"]):
        # Translate labels
        if item["label"][0:8] == "LOCALIZE":
            if not PY3:
                item["label"] = unicode(getLocalizedLabel(item["label"]), 'utf-8')
            else:
                item["label"] = getLocalizedLabel(item["label"])
                if isinstance(item["label"], bytes):
                    item["label"] = item["label"].decode("utf8")
        if item["label2"][0:8] == "LOCALIZE":
            item["label2"] = getLocalizedLabel(item["label2"])

        listItem = xbmcgui.ListItem(label=item["label"], label2=item["label2"])
        listItem.setArt({'icon': item["icon"]})
        listItem.setArt({'thumb': item["thumbnail"]})
        if item.get("info"):
            listItem.setInfo("video", item["info"])
        if item.get("stream_info"):
            for type_, values in list(item["stream_info"].items()):
                listItem.addStreamInfo(type_, values)
        if item.get("art"):
            listItem.setArt(item["art"])
        elif ADDON.getSetting('default_fanart') == 'true' and ((not PY3 and item["label"] != unicode(getLocalizedString(30218), 'utf-8')) or (PY3 and item["label"] != str(getLocalizedString(30218)))):
            fanart = os.path.join(ADDON_PATH, "fanart.jpg")
            listItem.setArt({'fanart': fanart})
        if item.get("context_menu"):
            # Translate context menus
            for m, menu in enumerate(item["context_menu"]):
                if menu[0][0:8] == "LOCALIZE":
                    menu[0] = getLocalizedLabel(menu[0])
            listItem.addContextMenuItems(item["context_menu"])
        listItem.setProperty("isPlayable", item["is_playable"] and "true" or "false")
        if item.get("properties"):
            for k, v in list(item["properties"].items()):
                listItem.setProperty(k, v)
        listitems[i] = (item["path"], listItem, not item["is_playable"])

    xbmcplugin.addDirectoryItems(HANDLE, listitems, totalItems=len(listitems))

    # Set ViewMode
    if data["content_type"]:
        viewMode = ADDON.getSetting("viewmode_%s" % data["content_type"])
        if viewMode:
            try:
                xbmc.executebuiltin('Container.SetViewMode(%s)' % viewMode)
            except Exception as e:
                log.warning("Unable to SetViewMode(%s): %s" % (viewMode, repr(e)))

    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=False, cacheToDisc=False)
