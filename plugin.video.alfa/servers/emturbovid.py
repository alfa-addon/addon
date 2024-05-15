# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Emturbovid By Alfa development Group
# --------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
from core import httptools
from platformcode import logger
from lib import jsunpack
from core import scrapertools

def test_video_exists(page_url):
    global data, server
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    data = response.data
    server = scrapertools.get_domain_from_url(page_url)
    if "<b>File not found, sorry!</b" in data:
        return False, "[Emturbovid] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    patron = "urlPlay\s*=\s*'([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        if not server in url:
            url = urlparse.urljoin(page_url,url)
        url += "|Referer=%s" %server
        video_urls.append(['[Emturbovid]', url])
    return video_urls

