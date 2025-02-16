# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from core import httptools
from core import scrapertools
from platformcode import logger
from bs4 import BeautifulSoup

#       https://swiftload.io/d/nmvq9hwfiyo Este falla 

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    reponse = httptools.downloadpage(page_url)
    data = reponse.data
    if reponse.code == 404 or "not found" in data or "no longer exists" in data or '"sources": [false]' in data:
        return False, "[swiftload] El archivo no existe o ha sido borrado"
    if "Still encoding" in data:
        return False, "[swiftload] El video todavía se está codificando ..."
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    logger.debug(soup)
    url = soup.source['src']
    video_urls.append(['[swiftload]', url])
    # m3u = soup.find('a', id="downloadNow")['href']
    # data = httptools.downloadpage(m3u).data
    # if PY3 and isinstance(data, bytes): data = data.decode()
    # patron = 'RESOLUTION=\d+x(\d+),.*?'
    # patron += 'NAME="([^"]+)"'
    # matches = re.compile(patron,re.DOTALL).findall(data)
    # for quality,url in matches:
        # url += ".m3u8"
        # url = m3u.replace("master.m3u8", url)
        # video_urls.append(['[swiftload] %sp' %quality, url])
    # video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

