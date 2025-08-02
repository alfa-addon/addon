# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    global data
    data = response.data
    if "Video not found" in data or "This video was deleted" in data \
        or "se ha eliminado" in data \
        or "acceso restringido" in data \
        or "access restricted" in data:
        return False, "[xhamster] El fichero no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    # patron = '\{"url":"([^"]+)","fallback":(?:"[^"]+"|),"quality":"(\d+p)",'
    patron = '\{"url":"([^"]+)","fallback":(?:"[^"]+"|""),"quality":"(\d+p)",'
    matches = scrapertools.find_multiple_matches(data, patron)
    patron2 = '"(\d+p)":\{"url":"([^"]+)"'
    matches2 = scrapertools.find_multiple_matches(data, patron2)
    pornstars = scrapertools.find_single_match(data, "&xprf=([^&]+)&").replace("+", " ").replace("%2C", " & ")
    logger.debug(pornstars)
    if not matches:
        for quality,url in matches2:
            url =  url.replace("\/", "/")
            if "referer=" in url: continue
            # url += "|Referer=%s&verifypeer=false" %page_url
            video_urls.append(["[xhamster] %s" %quality, url])
    for url,quality in matches:
        url =  url.replace("\/", "/")
        if "referer=" in url: continue
        # url += "|Referer=%s&verifypeer=false" %page_url
        video_urls.append(["[xhamster] %s" %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

