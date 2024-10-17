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
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    kwargs['headers'] = {'User-Agent':UA}
    response = httptools.downloadpage(page_url, **kwargs)
    global data, server, text
    server = scrapertools.get_domain_from_url(page_url)
    data = response.data
    # data = httptools.downloadpage(page_url).data
    # cookie = []
    # cook = scrapertools.find_multiple_matches(data, ".cookie\('([^']+)',\s*'([^']+)'")
    # for elem in cook:
        # cat = "%s=%s" %(elem[0],elem[1])
        # cookie.append(cat)
    # text = ';'.join(cookie)
    # kwargs['headers'] = {"Cookie": text}
    if not response.sucess or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False, "[lulustream] El fichero no existe o ha sido borrado"
    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    data = httptools.downloadpage(page_url, **kwargs).data
    url = scrapertools.find_single_match(data, 'sources: \[{file:"([^"]+)"')
    video_urls.append(["[lulustream]", url])
    return video_urls
