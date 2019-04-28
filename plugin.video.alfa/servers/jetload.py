# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector jetload By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[jetload] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    srv = scrapertools.find_single_match(data, 'id="srv" value="([^"]+)"')
    file_name = scrapertools.find_single_match(data, 'file_name" value="([^"]+)"')
    media_url = srv + "/v2/schema/%s/master.m3u8" %file_name
    video_urls.append([".MP4 [jetload]", media_url ])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
