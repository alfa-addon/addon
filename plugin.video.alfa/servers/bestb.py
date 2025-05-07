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
    
    global data, ref
    elem = page_url.split("|")
    url = elem[0]
    ref = elem[1]
    kwargs['headers'] = {
                         'Referer': ref,
                         'Origin': ref
                         # 'Sec-Fetch-Dest': 'iframe',
                         # 'Sec-Fetch-Mode': 'navigate',
                         # 'Sec-Fetch-Site': 'cross-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        }
    data = httptools.downloadpage(url, **kwargs).json
    
    if data.get('message', ''):
        return False, "[bestb] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # data = httptools.downloadpage(page_url, **kwargs).json
    
    m3u8_source = data['streaming_url'].replace("//master.m3u8", "/master.m3u8")
    
    kwargs['headers'] = {
                         'Referer': ref,
                         'Origin': ref
                         # 'Sec-Fetch-Dest': 'iframe',
                         # 'Sec-Fetch-Mode': 'navigate',
                         # 'Sec-Fetch-Site': 'cross-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        }
    
    if "master.m3u8" in m3u8_source:
        datos = httptools.downloadpage(m3u8_source, **kwargs).data
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                url =urlparse.urljoin(m3u8_source,url)
                url += "|Referer=%s/&Origin=%s" % (ref, ref)
                video_urls.append(['[bestb] %s' % quality, url])
    else:
        video_urls.append(["[bestb]", m3u8_source])
    return video_urls[::-1]
