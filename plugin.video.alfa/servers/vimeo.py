# -*- coding: utf-8 -*-

import sys
import re

from core import httptools
from core import scrapertools
from platformcode import logger
from core import urlparse


kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host = 'https://vimeo.com'


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    kwargs['headers'] = {
                         'Referer': '%s/' %page_url,
                         'Origin': page_url,
                         # 'Content-Type': 'application/json;charset=UTF-8',
                         # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                         # 'Sec-Fetch-Dest': 'empty',
                         # 'Sec-Fetch-Mode': 'cors',
                         # 'Sec-Fetch-Site': 'same-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        }
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "Lo sentimos" in response.data:
        return False,  "[vimeo] El fichero no existe o ha sido borrado"
    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    
    patron  = '"hls":.*?'
    patron += '"avc_url":"([^"]+)","origin"'
    m3u = scrapertools.find_single_match(data, patron)
    m3u = urlparse.unquote(m3u)
    m3u8_source = m3u.replace("\\u0026", "&")
    
    if httptools.downloadpage(m3u8_source, **kwargs).data:
        datos = httptools.downloadpage(m3u8_source, **kwargs).data
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                url =urlparse.urljoin(m3u8_source,url)
                url += "|Referer=%s/&Origin=%s" % (host, host)
                video_urls.append(['[vimeo] %sp' % quality, url])
            video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    else:
        m3u8_source += "|Referer=%s/&Origin=%s" % (host, host)
        video_urls.append(['[vimeo] m3u', m3u8_source])
    return video_urls

