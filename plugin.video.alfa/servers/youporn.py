# -*- coding: utf-8 -*-
# import sys
# PY3 = False
# if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

# if PY3:
    # import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
# else:
    # import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404 or "Not Found" in response.data:
        return False, "[Youporn] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    # url = urlparse.unquote(url)
    # id = scrapertools.find_single_match(page_url, '/(\d+)/')
    # url = "https://www.youporn.com/api/video/media_definitions/%s" % id
    data = httptools.downloadpage(page_url).data
    url = scrapertools.find_single_match(data, '"videoUrl":"([^"]+)"').replace("\/", "/").replace("%5C/", "/")
    data= httptools.downloadpage(url).json
    for elem in data:
        url = elem['videoUrl']
        if ",480P_" in url: continue
        quality = elem['quality']
        video_urls.append(["[youporn] %sp" %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

