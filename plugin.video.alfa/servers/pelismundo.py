# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Conector para pelismundo
# https://github.com/alfa-addon
# ------------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url, add_referer = True).data
    if "Object not found" in data or "no longer exists" in data or '"sources": [false]' in data or 'sources: []' in data:
        return False, "[pelismundo] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url, add_referer = True).data
    patron = 'sources.*?}],'
    bloque = scrapertools.find_single_match(data, patron)
    patron = 'file.*?"([^"]+)".*?label:"([^"]+)"'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedquality in match:
        video_urls.append([scrapedquality + " [pelismundo]", scrapedurl])
    #video_urls.sort(key=lambda it: int(it[0].split("p ", 1)[0]))
    return video_urls
