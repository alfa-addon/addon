# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidhide By Alfa development Group
# --------------------------------------------------------

import sys
import re

from core import httptools, jsontools
from core import scrapertools
from platformcode import logger
from lib import jsunpack
from core import urlparse

video_urls = []

# forced_proxy_opt = 'ProxySSL'
# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    if "|Referer" in page_url or "|referer" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {'Referer': referer}
    
    # page_url = httptools.downloadpage(page_url, follow_redirects=False).headers["location"]
    
    response = httptools.downloadpage(page_url, **kwargs)
    global data
    data = response.data
    if not response.sucess or "Not Found" in data or "File was deleted" in data \
                           or "is no longer available" in data:
        return False, "[vidhide] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    domain = scrapertools.get_domain_from_url(page_url)
    host = "https://%s" % domain
    try:
        enc_data = scrapertools.find_single_match(data, "text/javascript(?:'|\")>(eval.*?)</script>")
        dec_data = jsunpack.unpack(enc_data)
        # logger.debug("dec_data: %s" % dec_data)
        m3u8_source = scrapertools.find_single_match(dec_data,r'"hls\d":"([^"]+?\.m3u8[^"]+)')
        m3u8_source = urlparse.urljoin(host, m3u8_source)
        video_urls.append(['[vidhide] m3u', m3u8_source])
    except Exception as e:
        logger.error(str(e))
    return video_urls
