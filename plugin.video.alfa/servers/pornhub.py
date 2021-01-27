# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhub By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    global data
    data = response.data
    if not response.sucess or "Not Found" in data or "Video Disabled" in data or "<div class=\"removed\">" in data or "is unavailable" in data:
        return False, "[pornhub] El fichero no existe o ha sido borrado"
    else:
        data = scrapertools.find_single_match(data, '<div id="player"(.*?)</script>')
        data = data.replace('" + "', '')
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url= ""
    videourl = scrapertools.find_multiple_matches(data, 'var media_\d+=([^;]+)')
    for elem in videourl:
        orden = scrapertools.find_multiple_matches(elem, '\*\/([A-z0-9]+)')
        url= ""
        for i in orden:
            url += scrapertools.find_single_match(data, '%s="([^"]+)"' %i)
        if not "/get_media?" in url and not "urlset" in url:
            quality = scrapertools.find_single_match(url, '(\d+)P_')
            video_urls.append(["%sp [pornhub]" % quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

