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

###############   el embed en sourtype

      # {
        # "pattern": "((?:fuqer|dump).(?:com|xxx))/(?:vid|embed)/([0-9]+)",
        # "url": "https://www.\\1/embed/\\2"
      # }


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global host, server, data
    
    domain = scrapertools.get_domain_from_url(page_url)
    host = alfa_urlparse.urlunsplit(('https', u'{}'.format(domain), "", "", ""))
    server = domain.split(".")[-2]
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if data.get('message', ''):
        return False, "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global host, server, data
    
    
    if "dump" in server:
        media = scrapertools.find_single_match(data, 'defaultRaw\s*=\s*"([^"]+)"')
        tempo = scrapertools.find_single_match(data, 'ttlSeconds\s*=\s*(\d+)')
        media = media.replace("\/", "/")
        secure = "%s/admin/secure_link.php?path=%s&ttl=%s|Referer=%s/" %(host, media, tempo, host)
    else:
        media = scrapertools.find_single_match(data, 'signedMediaUri\s*=\s*"([^"]+)"')
        tempo = scrapertools.find_single_match(data, 'ttlSeconds\s*=\s*"([^"]+)"')
        media = media.replace("\/", "/")
        secure = "%s/secure_link.php?path=%s&ttl=%s|Referer=%s/" %(host, media, tempo, host)
        
    
    datos = httptools.downloadpage(secure, **kwargs).data
    
    datos = json.loads(datos)
    if isinstance(datos, str):
        datos = json.loads(datos)
    
    if datos["url"]:
        url = datos["url"]
        url = urlparse.urljoin(host,url)
        video_urls.append(["[%s]" %server, url])
    return video_urls
