# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Gupload By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    status = data.sucess
    data = data.data
    if status == False or 'Maintenance' in data:
        return False, "[Gupload] El video no existe o ha sido borrado"
    elif not status:
        return False, "[Gupload] Error al acceder al video"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    url = page_url.replace('/e/', '/e/hls/')
    url += '/720p.m3u8'
    video_urls.append(["[Gupload]", url])
    
    return video_urls
