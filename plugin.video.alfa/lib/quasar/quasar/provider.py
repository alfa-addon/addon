#from future import standard_library
#standard_library.install_aliases()
from future.builtins import map
from future.builtins import object
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.request as urllib2
    from urllib.parse import urlencode
else:
    import urllib2
    from urllib import urlencode

import json
import base64
from quasar.util import notify, getLocalizedString
from quasar.logger import log
from quasar.config import QUASARD_HOST
from quasar.addon import ADDON, ADDON_ID
from http.cookiejar import CookieJar


RESOLUTION_UNKNOWN = 0
RESOLUTION_480P = 1
RESOLUTION_720P = 2
RESOLUTION_1080P = 3
RESOLUTION_1440P = 4
RESOLUTION_4K2K = 5

RIP_UNKNOWN = 0
RIP_CAM = 1
RIP_TS = 2
RIP_TC = 3
RIP_SCR = 4
RIP_DVDSCR = 5
RIP_DVD = 6
RIP_HDTV = 7
RIP_WEB = 8
RIP_BLURAY = 9

RATING_UNKNOWN = 0
RATING_PROPER = 1
RATING_NUKED = 2

CODEC_UNKNOWN = 0
CODEC_XVID = 1
CODEC_H264 = 2
CODEC_H265 = 3
CODEC_MP3 = 4
CODEC_AAC = 5
CODEC_AC3 = 6
CODEC_DTS = 7
CODEC_DTSHD = 8
CODEC_DTSHDMA = 9

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"

COOKIE_JAR = CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(COOKIE_JAR)))


class closing(object):
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        return self.thing

    def __exit__(self, *exc_info):
        self.thing.close()


def parse_json(data):
    try:
        import simplejson as json
    except ImportError:
        import json
    return json.loads(data)


def parse_xml(data):
    import xml.etree.ElementTree as ET
    return ET.fromstring(data)


def request(url, params={}, headers={}, data=None, method=None):
    if params:
        url = "".join([url, "?", urlencode(params)])

    req = urllib2.Request(url)
    if method:
        req.get_method = lambda: method
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept-Encoding", "gzip")
    for k, v in list(headers.items()):
        req.add_header(k, v)
    if data:
        req.add_data(data)
    try:
        with closing(urllib2.urlopen(req)) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
            response.data = data
            response.json = lambda: parse_json(data)
            response.xml = lambda: parse_xml(data)
            return response
    except Exception as e:
        import traceback
        list(map(log.error, traceback.format_exc().split("\n")))
        notify("%s: %s" % (getLocalizedString(30224), repr(e).encode('utf-8')))
        return None, None


HEAD = lambda *args, **kwargs: request(*args, method="HEAD", **kwargs)
GET = lambda *args, **kwargs: request(*args, method="GET", **kwargs)
POST = lambda *args, **kwargs: request(*args, method="POST", **kwargs)
PUT = lambda *args, **kwargs: request(*args, method="PUT", **kwargs)
DELETE = lambda *args, **kwargs: request(*args, method="DELETE", **kwargs)


def append_headers(uri, headers):
    return uri + "|" + "|".join(["%s=%s" % h for h in list(headers.items())])


def with_cookies(uri):
    return uri + "|Cookie=" + "; ".join(["%s=%s" % (c.name, c.value) for c in COOKIE_JAR])


def extract_magnets(data):
    import re
    for magnet in re.findall(r'magnet:\?[^\'"\s<>\[\]]+', data):
        yield {"uri": magnet}


# Borrowed from xbmcswift2
def get_setting(key, converter=str, choices=None):
    value = ADDON.getSetting(id=key)
    if converter is str:
        return value
    elif converter is unicode:
        value = value.decode('utf-8')
        return value
    elif PY3 and converter is bytes:
        return value.decode('utf-8')
    elif converter is bool:
        return value == 'true'
    elif converter is int:
        return int(value)
    elif isinstance(choices, (list, tuple)):
        return choices[int(value)]
    else:
        raise TypeError('Acceptable converters are str, unicode, bool and '
                        'int. Acceptable choices are instances of list '
                        ' or tuple.')


def set_setting(key, val):
    return ADDON.setSetting(id=key, value=val)


def register(search, search_movie, search_episode, search_season=None):
    try:
        payload = json.loads(base64.b64decode(sys.argv[1]))
    except:
        notify(getLocalizedString(30102), time=1000)
        return

    results = ()
    method = {
        "search": search,
        "search_movie": search_movie,
        "search_season": search_season,
        "search_episode": search_episode,
    }.get(payload["method"]) or (lambda *a, **kw: [])
    try:
        results = ()
        try:
            objects = method(payload["search_object"])
            if objects is not None:
                results = tuple(objects)
        except Exception as e:
            import traceback
            list(map(log.error, traceback.format_exc().split("\n")))
            notify("%s: %s" % (getLocalizedString(30224), repr(e).encode('utf-8')))
            try:
                urllib2.urlopen("%s/provider/%s/failure" % (QUASARD_HOST, ADDON_ID))
            except:
                pass
    finally:
        try:
            req = urllib2.Request(payload["callback_url"], data=json.dumps(results))
            with closing(urllib2.urlopen(req)) as response:
                log.debug("callback returned: %d" % response.getcode())
        except Exception as e:
            import traceback
            list(map(log.error, traceback.format_exc().split("\n")))
            notify("%s: %s" % (getLocalizedString(30224), repr(e).encode('utf-8')))
            try:
                urllib2.urlopen("%s/provider/%s/failure" % (QUASARD_HOST, ADDON_ID))
            except:
                pass
