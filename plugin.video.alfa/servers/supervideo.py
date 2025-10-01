# -*- coding: utf-8 -*-

import sys
import re

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack
from core import urlparse

# kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host= "https://supervideo.cc"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
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
    
    # page_url = httptools.downloadpage(page_url, follow_redirects=False).headers["location"]
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if "File is no longer available as it expired or has been deleted" in data or "File Not Found" in data:
        return False, "[supervideo] El fichero ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    
    try:
        pack = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
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
                    video_urls.append(['[supervideo] %sp' % quality, url])
        else:
            video_urls.append(['[supervideo] m3u', m3u8_source])

    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
