# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhub By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "has been disabled" in data or "ha sido deshabilitado" in data:
        return False, "[pornhub] El video ha sido borrado o no existe"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = scrapertools.find_single_match(data, '<div id="player"(.*?)</script>')
    data = data.replace('" + "', '')
    url= ""
    videourl = scrapertools.find_multiple_matches(data, 'var media_\d+=([^;]+)')
    for elem in videourl:
        orden = scrapertools.find_multiple_matches(elem, '\*\/([A-z0-9]+)')
        url= ""
        for i in orden:
            url += scrapertools.find_single_match(data, '%s="([^"]+)"' %i)
        if not ".m3u8" in url:
            quality = scrapertools.find_single_match(url, '/(\d+)P_[A-z0-9_]+.mp4')
            video_urls.append(["%sp [pornhub]" % quality, url])
    return video_urls

