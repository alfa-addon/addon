# Conector tiwikiwi By Alfa development Group
# --------------------------------------------------------

import sys
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse


kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


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
    # server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    
    # page_url = httptools.downloadpage(page_url, follow_redirects=False).headers["location"]
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "not found" in response.data:
        return False,  "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)
        
        # m3u8_source = scrapertools.find_single_match(unpacked, '\{(?:file|"hls\d+"):"([^"]+)"\}')
        m3u8_source = scrapertools.find_single_match(unpacked, '\{(?:file|"hls\d+"|src):"([^"]+)"')
        
        if "master.m3u8" in m3u8_source:
            datos = httptools.downloadpage(m3u8_source, **kwargs).data
            if sys.version_info[0] >= 3 and isinstance(datos, bytes):
                datos = "".join(chr(x) for x in bytes(datos))
            
            if datos:
                matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                for quality, url in matches_m3u8:
                    url =urlparse.urljoin(m3u8_source,url)
                    url += "|Referer=%s/&Origin=%s" % (host, host)
                    video_urls.append(['[%s] %s' % (server, quality), url])
        else:
            video_urls.append(['[%s] m3u' %server, m3u8_source])

    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
