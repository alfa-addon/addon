# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404 or "has been flagged" in data or "Disabled Video" in response.data \
        or "Removed Video" in response.data or "Inactive Video" in response.data:
        return False, "[tube8] El archivo no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data, server
    
    url = scrapertools.find_single_match(data, '"format":"mp4",.*?"videoUrl":"([^"]+)"').replace("\/", "/")
    data = httptools.downloadpage(url).json
    for elem in data:
        quality = elem['quality']
        url = elem['videoUrl']
        video_urls.append(["[tube8] %sp" %quality, url])
    return video_urls[::-1]
