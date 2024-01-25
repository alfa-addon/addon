# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mydaddy By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404 or "Not Found" in data \
       or "File was deleted" in data \
       or "is no longer available" in data:
        return False, "[mydaddy] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace("\\", "")
    orden = scrapertools.find_single_match(data, '.replaceAll\(([^\)]+)')
    orden = orden.replace('"', '').replace('+', ',')
    orden = orden.split(",")
    matches = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" title="([^"]+)"')
    for url,quality in matches:
        s1 = scrapertools.find_single_match(data, '%s="([^"]+)"' %orden[1])
        s2 = orden[2]
        s3 = scrapertools.find_single_match(data, '%s="([^"]+)"' %orden[3])
        s4 = orden[4]
        s5 = url.replace(orden[0], "")
        url = "https:%s%s%s%s%s" % (s1,s2,s3,s4,s5)
        if not "Default" in quality:
            quality = quality.replace("p60", "p")
        video_urls.append(["[mydaddy] %s" % quality, url])
    return video_urls

