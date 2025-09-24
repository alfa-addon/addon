# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamwish By Alfa Development Group
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

# https://wishonly.site/e/4ihupegt08mc 
# https://jwplayerhls.com/e/ot7d0acd0ct3  720 y 1080
# https://streamwish.to/e/g00srkwf3uj0|Referer=https://pubjav.com/  480 720 1080


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    
    if sys.version_info >= (3,):
        from lib import alfaresolver_py3 as revolver
    else:
        from lib import alfaresolver as revolver
    
    if "|Referer" in page_url or "|referer" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {'Referer': referer}
    
    # page_url = httptools.downloadpage(page_url, follow_redirects=False).headers["location"]
    
    response = httptools.downloadpage(revolver.wishmeluck(page_url), **kwargs)
    data = response.data
    
    if response.code == 404 or "no longer available" in data or "Not Found" in data: 
        return False, "[streamwish] El archivo no existe o ha sido borrado"
    if "restricted for this domain" in data:
        return False, "[streamwish] El archivo esta restringido en tu pais"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)
        
        # m3u8_source = scrapertools.find_single_match(unpacked, '\{(?:file|"hls\d+"):"([^"]+)"\}')
        m3u8_source = scrapertools.find_single_match(unpacked, '(?:file|"hls2"):"([^"]+)"') ##evitar "hls4"
        
        subtitles = ''
        vttreg = re.compile('file:"([^"]+)",label:')
        subs = vttreg.findall(unpacked)
        if subs:
            for sub in subs:
                subtitles += sub + "\n"
        
        video_urls.append(["[streamwish] .m3u8", m3u8_source, 0, subtitles])
    
    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
