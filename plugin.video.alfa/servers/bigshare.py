# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector bigshare By Alfa Development Group
# --------------------------------------------------------

import sys
import re

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from lib import jsunpack

# forced_proxy_opt = 'ProxySSL'
# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}




def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if response.code == 404 or "no longer available" in data or "Not Found" in data: 
        return False, "[bigshare] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    url = scrapertools.find_single_match(data, "url:\s*'([^']+)'")
    video_urls.append(["[bigshare]", url])
    
    return video_urls
