# -*- coding: utf-8 -*-

import sys
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
    
    global data
    # kwargs['headers'] = {
                         # 'Referer': ref,
                         # 'Origin': ref
                         # 'Sec-Fetch-Dest': 'iframe',
                         # 'Sec-Fetch-Mode': 'navigate',
                         # 'Sec-Fetch-Site': 'cross-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        # }
    data = httptools.downloadpage(page_url, **kwargs).data
    if data.get('message', ''):
        return False, "[porntopedia] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # global data
    patron = '"contentUrl":\s*"([^"]+)"'
    url = scrapertools.find_single_match(data, patron)
    video_urls.append(["[porntopedia]", url])
    return video_urls#[::-1]
