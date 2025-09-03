# -*- coding: utf-8 -*-

import sys
import re

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host = "https://xhamster.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    response = httptools.downloadpage(page_url)
    data = response.data
    # logger.debug(data)
    if "Video not found" in data or "This video was deleted" in data \
        or "se ha eliminado" in data \
        or "acceso restringido" in data \
        or "access restricted" in data:
        return False, "[xhamster] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # logger.debug(scrapertools.find_single_match(data, '("sources"\:\{.*?),"userSettings"'))
    m3u8_source = ""
    patron = '"av1":\{"url":"([^"]+)"'
    m3u8_source = scrapertools.find_single_match(data, patron)
    if not m3u8_source:
        patron = '"h264":\{"url":"([^"]+)"'
        m3u8_source = scrapertools.find_single_match(data, patron)
    if not m3u8_source:
        patron = '"(\d+p)":\{"url":"([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for quality, url in matches:
            url = url.replace("\/","/")
            video_urls.append(['[xhamster] %s' % quality, url])
    if m3u8_source:
        m3u8_source = m3u8_source.replace("\/", "/")
        kwargs['headers'] = {
                             'Referer': '%s/' % host,
                             'Origin': host,
                            }
        datos = httptools.downloadpage(m3u8_source, **kwargs).data
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        if datos:
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                url =urlparse.urljoin(m3u8_source,url)
                # url += "|Referer=%s" % host
                url += "|Referer=%s/&Origin=%s" % (host, host)
                video_urls.append(['[xhamster] %s' % quality, url])
    
    pornstars = scrapertools.find_single_match(data, "&xprf=([^&]+)&").replace("+", " ").replace("%2C", " & ")
    logger.debug(pornstars)
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

