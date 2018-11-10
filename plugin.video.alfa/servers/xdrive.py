# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Conector para xdrive
# https://github.com/alfa-addon
# ------------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Object not found" in data or "no longer exists" in data or '"sources": [false]' in data:
        return False, "[xdrive] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data1 = httptools.downloadpage("https://xdrive.cc/geo_ip").data
    _ip = scrapertools.find_single_match(data1, 'ip":"([^"]+)')
    data = httptools.downloadpage(page_url).data
    video_id = scrapertools.find_single_match(data, '&video_id=(\d+)')
    data = httptools.downloadpage("https://xdrive.cc/secure_link?ip=%s&video_id=%s" %(_ip, video_id)).data.replace("\\","")
    videourl = scrapertools.find_multiple_matches(data, '"([^"]+)"')
    for scrapedurl in videourl:
        video_urls.append(["[xdrive]", scrapedurl])
    return video_urls
