# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector videossh By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[videossh] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron = 'file:"([^"]+)"'
    match = scrapertools.find_multiple_matches(data, patron)
    for media_url in match:
        media_url += "|Referer=%s" %page_url
        title = "mp4 [videossh]"
        video_urls.append([title, media_url])
    return video_urls
