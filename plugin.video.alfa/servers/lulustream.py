# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector lulustream By Alfa development Group
# --------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
from core import httptools, jsontools
from core import scrapertools
from platformcode import logger

video_urls = []
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.8464.47 Safari/537.36 OPR/117.0.8464.47"

#Error al reproducir
# https://lulustream.com/e/j8b5qhy00rjs

# https://cdn1024.tnmr.org/hls2/01/00376/j8b5qhy00rjs_h/master.m3u8?t=IucdKwlOSIWMseVDZkz-fr-F7uGk8DZd2lAMIe-1YGQ&s=1728507883&e=43200&f=1883521&i=0.3&sp=0|User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F117.0.8464.47+Safari%2F537.36+OPR%2F117.0.8464.47&Referer=https%3A%2F%2Flulustream.com%2F&Origin=https%3A%2F%2Flulustream.com|{}|

# https://cdn1024.tnmr.org/hls2/01/00376/j8b5qhy00rjs_h/master.m3u8?t=IucdKwlOSIWMseVDZkz-fr-F7uGk8DZd2lAMIe-1YGQ&s=1728507883&e=43200&f=1883521&i=0.3&sp=0|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.8464.47 Safari/537.36 OPR/117.0.8464.47&Referer=https://lulustream.com/&Origin=https://lulustream.com

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    kwargs['headers'] = {'User-Agent':UA}
    response = httptools.downloadpage(page_url, **kwargs)
    global data, server, text
    server = scrapertools.get_domain_from_url(page_url)
    data = response.data
    cookie = []
    data = httptools.downloadpage(page_url).data
    cook = scrapertools.find_multiple_matches(data, ".cookie\('([^']+)',\s*'([^']+)'")
    for elem in cook:
        cat = "%s=%s" %(elem[0],elem[1])
        cookie.append(cat)
    text = ';'.join(cookie)
    kwargs['headers'] = {"Cookie": text}
    if not response.sucess or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False, "[lulustream] El fichero no existe o ha sido borrado"
    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # kwargs['headers'] = {'User-Agent':UA, "Cookie": text}
    # kwargs['headers'] = {'User-Agent':UA}
    data = httptools.downloadpage(page_url, **kwargs).data
    
    url = scrapertools.find_single_match(data, 'sources: \[{file:"([^"]+)"')
    # url += '|'
    # url += urlparse.urlencode(httptools.default_headers)
    url += "|User-Agent=%s&Referer=https://lulustream.com/&Origin=https://lulustream.com|{}" %UA
    
    # url +='|User-Agent=%s&Referer=https://%s/&Origin=https://%s' % (httptools.get_user_agent(), server,server)
    video_urls.append(["[lulustream]", url])
   
    # kwargs['headers'] = {"Referer": "https://%s/" %server, "Origin": "https://%s" %server}
    # datos = httptools.downloadpage(url).data
    # if PY3 and isinstance(datos, bytes):
        # datos = "".join(chr(x) for x in bytes(datos))
            
    # if datos:
        # matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
        # for quality, url in matches_m3u8:
             # Mozilla/5.0 (Windows NT 10.0; Win64; x64)
            # url +='|User-Agent=%s&Referer=%s' % (httptools.get_user_agent(), page_url)
            # url += "|User-Agent=Mozilla/5.0 %28Windows NT 10.0%3B Win64%3B x64%3B rv%3A109.0%29+Gecko/20100101 Firefox/117.0&Referer=https://%s/&Origin=https://%s" %(server,server)
            # url += "|Referer=https://%s/" %url  #server page_url url 
            # url += "|Origin=https://%s" %server
            # url += "|verifypeer=false"
            # url += '/:?=&'
            # video_urls.append(["[lulustream] %s" % quality, url])
    return video_urls
