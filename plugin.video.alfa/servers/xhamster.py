# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    global m3u
    data = response.data
    data = scrapertools.find_single_match(data, '{"mp4":\[(.*?)\]\},')
    if not response.sucess or "Video not found" in data or "access restricted " in data or "ha sido deshabilitado" in data or "is unavailable" in data:
        return False, "[xhamster] El fichero no existe o ha sido borrado"
    url = scrapertools.find_single_match(data, '{"url":"([^"]+)"')
    m3u =  url.replace("\/", "/")
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = "https://xhamster.com%s" % m3u
    data = httptools.downloadpage(url).data
    patron = ',NAME="([0-9]+p)".*?(https:.*?)\\n'
    matches = scrapertools.find_multiple_matches(data, patron)
    for quality,url in matches:
        url =  url.replace("\/", "/")
        video_urls.append(["[xhamster] %s" %quality, url])
    return video_urls[::-1]

