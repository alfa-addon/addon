# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data or "to copyright issues" in data:
        return False, "[clipwatching] El video ha sido borrado"
    if "please+try+again+later." in data:
        return False, "[clipwatching] Error de clipwatching, no se puede generar el enlace al video"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    video_urls = []
    videourl, label = scrapertools.find_single_match(data, 'file:"([^"]+).*?label:"([^"]+)')
    video_urls.append([label + " [clipwatching]", videourl])

    return video_urls
