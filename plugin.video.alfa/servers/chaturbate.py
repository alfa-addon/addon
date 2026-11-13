# -*- coding: utf-8 -*-
from core import urlparse as alfa_urlparse
import re
from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from core.jsontools import json
from bs4 import BeautifulSoup

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host= "https://chaturbate.com"


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    response = httptools.downloadpage(page_url, **kwargs)
    # logger.debug(response.headers)
    data = response.data
    
    if data.get('message', ''):
        return False, "[chaturbate] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    headers = httptools.default_headers.copy()
    
    initialRoomDossier = scrapertools.find_single_match(data, 'window.initialRoomDossier\s+=\s+([^;]+)')
    datos = json.loads(initialRoomDossier)
    if isinstance(datos, str):
        datos = json.loads(datos)
    if datos["hls_source"]:
        url = datos["hls_source"]
        url = alfa_urlparse.add_url_headers(url, headers, {'Referer': u'{}/'.format(u'{}'.format(host)), 'Origin': u'{}'.format(host)})
        video_urls.append(["[chaturbate]", url])
    return video_urls
