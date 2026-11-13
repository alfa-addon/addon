# -*- coding: utf-8 -*-
# -*- Server vidara -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import urlparse as alfa_urlparse
import sys
from core import httptools
from core import scrapertools
from platformcode import logger
from core import urlparse
from bs4 import BeautifulSoup

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

# https://www.tubeonline.net/pelicula/maquina-de-guerra/  https://krakenfiles.com/embed-video/iINeJMTAKQ

host = "https://krakenfiles.com" 


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if response.code == 404  or "File Not Found" in data or "File is no longer available" in data:
        return False, "[krakenfiles] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    headers = httptools.default_headers.copy()
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    if soup.video.source:
        tipo = soup.video.source['type']    # application/x-mpegURL & video/mp4
    matches  = soup.find('source', type=tipo)
    url = matches.get('src', '') 
    url = alfa_urlparse.add_url_headers(url, headers, {'Referer': u'{}/'.format(u'{}'.format(host)), 'Origin': u'{}'.format(host)})
    video_urls.append(["[krakenfiles]", url])
    
    return video_urls

