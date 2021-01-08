# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector redtube By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    global data
    response = httptools.downloadpage(page_url)
    if not response.sucess or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "This video has been removed" in response.data \
       or "Video has been flagged for verification" in response.data \
       or "is no longer available" in response.data:
        return False, "[redtube] El fichero no existe o ha sido borrado"
    data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    video_urls = []
    data2 = scrapertools.find_single_match(data,'mediaDefinition: \[(.*?)\]')
    patron  = '"defaultQuality":.*?,"quality":"([^"]+)","videoUrl"\:"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data2, patron)
    for quality,scrapedurl  in matches:
        url =  scrapedurl.replace("\/", "/")
        video_urls.append(["[redtube] %sp" %quality, url])
    return video_urls