# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector bunkr By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    data = httptools.downloadpage(page_url)
    status = data.sucess
    data = data.data
    
    if status == False or 'Maintenance' in data:
        return False, "[bunkr] El video no existe o ha sido borrado"
    elif not status:
        return False, "[bunkr] Error al acceder al video"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    
    url = scrapertools.find_single_match(data, r"jsCDN\s*=\s*'([^']+)'")
    post = url.split('storage')[-1]
    post = "\/storage%s" %post
    post = post.replace('\/', "%2F")
    
    post_url = "https://glb-apisign.cdn.cr/sign?path=%s" %post
    datos = httptools.downloadpage(post_url).json
    
    url= url.replace("\/", "/") 
    url += '?token=%s&ex=%s' %(datos['token'], datos['ex'])
    video_urls.append(["[bunkr]", url])
    
    return video_urls
