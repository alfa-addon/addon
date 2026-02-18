# Conector all4tube By Alfa development Group
# --------------------------------------------------------

import sys
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse

forced_proxy_opt = ''  #'ProxySSL'

# kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 1, #'forced_proxy_ifnot_assistant': forced_proxy_opt,
          'ignore_response_code': True, 'cf_assistant': False, 'CF_stat': True, 'CF': True,
          'timeout': 15}

host = "https://all4tube.com/"
server = "all4tube"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    
    id = scrapertools.find_single_match(page_url, '/e/([a-z0-9]+)')
    logger.debug(id)
    post = {'op': 'embed', 'file_code': id, 'auto': 1, 'referer': ''}
    post_url = "%sdl" % host
    
    response = httptools.downloadpage(post_url, post=post, **kwargs)
    data = response.data
    
    if response.code == 404 or "not found" in response.data or "no longer available" in response.data:
        return False,  "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        # packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
        packed = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        logger.debug(packed)
        unpacked = jsunpack.unpack(packed)
        logger.debug(unpacked)
        # m3u8_source = scrapertools.find_single_match(unpacked, '\{(?:file|"hls\d+"):"([^"]+)"\}')
        m3u8_source = scrapertools.find_single_match(unpacked, '(?:file|"hls2"|src):"([^"]+)"')
        
        
        # if "master.m3u8" in m3u8_source:
            # datos = httptools.downloadpage(m3u8_source, **kwargs).data
            
            # if sys.version_info[0] >= 3 and isinstance(datos, bytes):
                # datos = "".join(chr(x) for x in bytes(datos))
            # logger.debug(datos)
            # if datos:
                # matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                # matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                # for quality, url in matches_m3u8:
                    # url =urlparse.urljoin(m3u8_source,url)
                    # url += "|Referer=%s/&Origin=%s" % (host, host)
                    # video_urls.append(['[%s] %s' % quality, url])
        # else:
        video_urls.append(['[%s] m3u' %server, m3u8_source])

    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
