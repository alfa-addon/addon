# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector tnaflix By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    response = httptools.downloadpage(page_url)
    global data
    
    data = response.json
    
    if response.code == 404 or "Page not Found" in response.data \
                            or "File was deleted" in response.data \
                            or "video is a private" in response.data \
                            or "is no longer available" in response.data:
        return False, "[tnaflix] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(page_url).json
    data = data['html']
    patron = '<source src="([^"]+)".*?'
    patron += 'size="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, quality in matches:
        url= url.replace("![CDATA[", "").replace("]]", "")
        if not url.startswith("https"):
            url = "https:%s" % url
        itemlist.append(["[tnaflix] %s" % (quality), url])
    return itemlist[::-1]

