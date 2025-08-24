# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector asiananal By Alfa Development Group
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
        return False, "[asiananal] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    m3u8_source = scrapertools.find_single_match(data, 'streaming_url:"([^"]+)"')
    
    if "master.m3u8" in m3u8_source:
        datos = httptools.downloadpage(m3u8_source).data
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                url =urlparse.urljoin(m3u8_source,url)
                video_urls.append(["[asiananal] %sp" % quality, url])
    
    return video_urls[::-1]
