# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger

# https://xiaoshenke.net/video/ac28d00924929122ff/13   ##fullporner
# https://xiaoshenke.net/vid/ff22192942900d82ca/360

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    
    data = httptools.downloadpage(page_url).data
    
    if "<h2>WE ARE SORRY</h2>" in data or 'Not Found' in data:
        return False, "[xiaoshenke] El fichero no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    id = scrapertools.find_single_match(page_url, 'video(?:x|h|)/([A-z0-9]+)')
    id = id[::-1]
    
    data = httptools.downloadpage(page_url).data
    matches = scrapertools.find_multiple_matches(data, 'res.push\((\d+)')
    for quality in matches:
        url = "https://xiaoshenke.net/vid/%s/%s" %(id, quality)
        video_urls.append(["[xiaoshenke] %sp" % quality, url])
    return video_urls
