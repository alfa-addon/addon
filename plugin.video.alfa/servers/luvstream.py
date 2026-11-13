# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Conector luvstream (uno de los reproductores de bestporn4free).
#
# La pagina del embed es un HTML5 normal: <video><source src="https://cdn.luvstream.cc/
# media/<id>/<fichero>.mp4?md5=...&expire=..."></video>. El mp4 se sirve sin cabeceras
# especiales (medido el 2026-10-28: 200 video/mp4).
#------------------------------------------------------------
from core import urlparse as alfa_urlparse
import re

try:
    from html import unescape
except ImportError:                                              # Python 2
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape

from core import httptools
from platformcode import logger


kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 1,
          'ignore_response_code': True, 'timeout': 45, 'cf_assistant': False,
          'CF_stat': True, 'CF': True}

host = "https://luvstream.cc"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CABECERAS = "Referer=%s/&User-Agent=%s" % (host, _UA.replace(' ', '%20'))

FUENTE = re.compile(r'<(?:source|video)[^>]+src="([^"]+)"', re.I)


def _texto(datos):
    if isinstance(datos, bytes):
        datos = datos.decode('utf-8', 'replace')
    return datos or ''


def _fuente(page_url):
    data = _texto(httptools.downloadpage(page_url, headers={'User-Agent': _UA}, **kwargs).data)
    trozo = FUENTE.search(data)
    if not trozo:
        return ''
    url = unescape(trozo.group(1)).strip()
    if not url.startswith('http'):
        url = alfa_urlparse.build_url(host, u'/{}'.format(url.lstrip('/')))
    return url


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    if not _fuente(page_url):
        return False, "[COLOR red][luvstream] No hay video en esa pagina[/COLOR]"
    return True, ""


def get_video_url(page_url, video_password=""):
    logger.info("(page_url='%s')" % page_url)

    url = _fuente(page_url)
    if not url:
        return []

    return [["[luvstream]", alfa_urlparse.add_url_headers(url, alfa_urlparse.Headers.from_string(CABECERAS))]]
