# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector lulustream By Alfa development Group
# --------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
from core import httptools, jsontools
from core import scrapertools
from platformcode import logger

video_urls = []
kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

#Error al reproducir
# https://lulustream.com/e/j8b5qhy00rjs
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url, **kwargs)
    global data, server
    server = scrapertools.get_domain_from_url(page_url)
    data = response.data
    cookie = []
    data = httptools.downloadpage(page_url).data
    cook = scrapertools.find_multiple_matches(data, ".cookie\('([^']+)',\s*'([^']+)'")
    for elem in cook:
        cat = "%s=%s" %(elem[0],elem[1])
        cookie.append(cat)
    text = ';'.join(cookie)
    kwargs['headers'] = {"Cookie": text}
    if not response.sucess or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False, "[lulustream] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url, **kwargs).data
    
    url = scrapertools.find_single_match(data, 'sources: \[{file:"([^"]+)"')
    kwargs['headers'] = {"Referer": "https://%s/" %server, "Origin": "https://%s" %server}
    datos = httptools.downloadpage(url).data
    if PY3 and isinstance(datos, bytes):
        datos = "".join(chr(x) for x in bytes(datos))
            
    if datos:
        matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
        for quality, url in matches_m3u8:
            url += "|Referer=https://%s/" %url  #server page_url url 
            # url += "|Origin=https://%s" %server
            url += "|verifypeer=false"
            # url += '/:?=&'
            video_urls.append(["[lulustream] %s" % quality, url])
    return video_urls
