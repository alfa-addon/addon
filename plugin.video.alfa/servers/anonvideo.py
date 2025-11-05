# Conector tiwikiwi By Alfa development Group
# --------------------------------------------------------

import sys
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse


kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 1,
          'ignore_response_code': True, 'cf_assistant': False, 'CF_stat': True, 'CF': True,
          'timeout': 15}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, host, server
    
    domain = scrapertools.get_domain_from_url(page_url)
    host = "https://%s" % domain
    server = domain.split(".")[-2]
    
    kwargs['headers'] = {
                         'Referer': '%s/' %host,
                         'Origin': host,
                         # 'Content-Type': 'application/json;charset=UTF-8',
                         # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                         # 'Sec-Fetch-Dest': 'empty',
                         # 'Sec-Fetch-Mode': 'cors',
                         # 'Sec-Fetch-Site': 'same-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        }
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if response.code == 404 or "not found" in response.data:
        return False,  "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    url = scrapertools.find_single_match(data, "file:\s*'([^']+)'")
    url += "|Referer=%s/&Origin=%s" % (host, host)
    
    video_urls.append(['[%s]' % (server), url])
    return video_urls
