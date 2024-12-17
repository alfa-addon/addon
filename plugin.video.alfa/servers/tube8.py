# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    # server = scrapertools.find_single_match(page_url, '//(?:www.|es.|)([A-z0-9-]+).(?:to|ws|net|com)')
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404 or "has been flagged" in data:
        return False, "[%s] El archivo no existe o ha sido borrado" %server
    return True, ""

def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    url = scrapertools.find_single_match(data, '"format":"mp4",.*?"videoUrl":"([^"]+)"').replace("\/", "/")
    data = httptools.downloadpage(url).json
    for elem in data:
        quality = elem['quality']
        url = elem['videoUrl']
        video_urls.append(["[tube8] %sp" %quality, url])
    return video_urls[::-1]
