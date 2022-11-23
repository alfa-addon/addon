# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamlare By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import logger

url_new = ''


def test_video_exists(page_url):
    global url_new
    logger.info("(page_url='%s')" % page_url)
    
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[streamlare] El fichero no existe o ha sido borrado"
    url_new = response.url or ''
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    global url_new
    
    video_urls = []
    matches = []
    
    if not url_new:
        id = scrapertools.find_single_match(page_url,'/e/(\w+)')
        post = {"id": id}
        
        response = httptools.downloadpage("https://streamlare.com/api/video/stream/get", post=post)
        data = response.data.replace("\\","")
        if response.url_new:
            url_new = response.url_new
            matches.append(['', url_new])
        else:
            matches = scrapertools.find_multiple_matches(data, 'label":"([^"]+).*?file":"([^"]+)')
    else:
        matches.append(['', url_new])
    
    for res, media_url in matches:
        media_url += "|User-Agent=%s" %(httptools.get_user_agent())
        video_urls.append([res, media_url])

    return video_urls
