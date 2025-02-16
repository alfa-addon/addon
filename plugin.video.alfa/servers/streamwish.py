# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamwish By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from lib import jsunpack

# forced_proxy_opt = 'ProxySSL'
# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

# https://wishonly.site/e/4ihupegt08mc 
# https://jwplayerhls.com/e/ot7d0acd0ct3  720 y 1080
# https://streamwish.to/e/g00srkwf3uj0|Referer=https://pubjav.com/


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    if "|Referer" in page_url or "|referer" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {'Referer': referer}
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "no longer available" in data or "Not Found" in data: 
        return False, "[streamwish] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)

        m3u8_source = scrapertools.find_single_match(unpacked, '\{file:"([^"]+)"\}')
        
        if "master.m3u8" in m3u8_source:
            datos = httptools.downloadpage(m3u8_source).data
            if isinstance(datos, bytes):
                datos = "".join(chr(x) for x in bytes(datos))
            
            if datos:
                matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                for quality, url in matches_m3u8:
                    url =urlparse.urljoin(m3u8_source,url)
                    video_urls.append(["[streamwish] %sp" % quality, url])
        else:
            video_urls.append(["[streamwish]", m3u8_source])

    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
