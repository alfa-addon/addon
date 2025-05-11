# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from bs4 import BeautifulSoup

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data,vid
    
    vid = page_url.split("|")
    url = vid[0]
    vid = vid[1]
    
    data = httptools.downloadpage(url, **kwargs).json
    
    if not 'public' in data["item"]['status']:
        return False, "[COLOR red][stripchat] Estoy en privado[/COLOR]"
    
    response = httptools.downloadpage(vid, **kwargs)
    if response.code == 404 or response.code == 401:
        return False, "[stripchat] El fichero no existe o ha sido borrado"
    
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    vid = page_url.split("|")
    url = vid[0]
    vid = vid[1]
    
    data = httptools.downloadpage(url, **kwargs).json
    data = data["item"]
    # isBlocked = data['isBlocked']
    # status = data['status']
    # isLive = data['isLive']
    
    if data['settings'].get('presets', ''):
        txt = data['settings']['presets'][:-1][::-1]
        for quality in txt:
            url = vid.replace(".m3u8", "_%s.m3u8" %quality)
            video_urls.append(["[stripchat] %s" %quality, url])
    else:
        video_urls.append(["[stripchat]", vid])
    return video_urls
