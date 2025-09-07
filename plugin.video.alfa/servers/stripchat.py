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

host = "https://stripchat.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global url,vid,data
    
    vd = page_url.split("|")
    url = vd[0]
    vid = vd[1]
    
    data = httptools.downloadpage(url, **kwargs).json
    
    if not 'public' in data["item"]['status']:
        return False, "[COLOR red][stripchat] Estoy en privado[/COLOR]"
    
    response = httptools.downloadpage(vid, **kwargs)
    if response.code == 404 or response.code == 401:
        return False, "[stripchat] El fichero no existe o ha sido borrado"
    
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global url,vid,data
    
    data = data["item"]
    
    # isBlocked = data['isBlocked']
    # status = data['status']
    # isLive = data['isLive']
    
    if data['settings'].get('presets', ''):
        datos = httptools.downloadpage(vid, **kwargs).data
        logger.debug(datos)
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            #EXT-X-MOUFLON:PSCH:v1:Zokee2OhPh9kugh4
            psch = scrapertools.find_single_match(datos, ":PSCH:([A-z0-9:]+)")
            psch = psch.split(":")
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ## matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                ## url =urlparse.urljoin(m3u8_source,url)
                url += "?psch=%s&pkey=%s&playlistType=lowLatency" %(psch[0],psch[1])
                url += "|Referer=%s/&Origin=%s" % (host, host)
                # url += "|Referer=%s/" % host
                video_urls.append(["[stripchat] %sp" % quality, url])
    
    else:
        # url += "|Referer=%s/&Origin=%s" % (host, host)
        video_urls.append(["[stripchat]", vid])
    return video_urls
