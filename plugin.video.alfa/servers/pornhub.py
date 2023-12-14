# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhub By Alfa development Group
# --------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
import time
from core import httptools
from core import scrapertools
from platformcode import logger
from core import jsontools as json

count = 4
retries = count

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'ignore_response_code': True, 'cf_assistant': False}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    headers = {'Referer': page_url}
    response = httptools.downloadpage(page_url, headers=headers, **kwargs)
    data = response.data
    if not response.sucess or "Not Found" in data or "flagged for  " in data or "Video Disabled" in data or "<div class=\"removed\">" in data or "is unavailable" in data:
        return False, "[pornhub] El fichero no existe o ha sido borrado"
    if "premiumLocked" in data:
        return False, "[pornhub] Cuenta premium"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    global retries
    # retries = count
    logger.info("(page_url='%s'; retry=%s)" % (page_url, retries))
    video_urls = []
    headers = {'Referer': page_url}
    data = httptools.downloadpage(page_url, headers=headers, **kwargs).data
    flashvars = scrapertools.find_single_match(data, '(var flashvars.*?)</script>')
    flashvars = flashvars.replace('" + "', '' ).replace("\/", "/")
    videos = scrapertools.find_single_match(flashvars, '"mediaDefinitions":(.*?),"isVertical"')
    crypto = scrapertools.find_multiple_matches(flashvars, "(var\sra[a-z0-9]+=.+?);flash")
    if not crypto:
        if not scrapertools.find_single_match(videos, (".m3u8\?validfrom\=")) and retries >= 0:
            retries -= 1
            if retries >= 0:
                time.sleep(count - retries)
                return get_video_url(page_url)
        
        JSONData = json.load(videos)
        for elem in JSONData:
            url = elem['videoUrl']
            type = elem['format']
            quality = elem['quality']
            if 'hls' in type and "validfrom=" in url and not "urlset" in url:
                video_urls.append(["[pornhub] m3u %s" % quality, url])
            # elif "urlset" in url:
                # video = url
                # data =  httptools.downloadpage(url, headers=headers, **kwargs).data
                # if PY3 and isinstance(data, bytes): data = data.decode()
                # patron = 'RESOLUTION=\d+x(\d+).*?CODECS="[^"]+"\s*([^\s]+)'
                # matches = re.compile(patron,re.DOTALL).findall(data)
                # for quality,url in matches:
                    # url = urlparse.urljoin(video,url)
                    # video_urls.append(["[pornhub] m3u %s" % quality, url])
            video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
            # if "get_media" in url:
                # video_json = httptools.downloadpage(url, set_tls=True, set_tls_min=True).json
                # for video in video_json:
                    # url = video['videoUrl']
                    # quality = video['quality']
                    # video_urls.append(["[pornhub] mp4 %sP" % quality, url])
    else:
        for elem in crypto:
            orden = scrapertools.find_multiple_matches(elem, '\*\/([A-z0-9]+)')
            url= ""
            quality = ""
            for i in orden:
                url += scrapertools.find_single_match(elem, '%s="([^"]+)"' %i)
            quality = scrapertools.find_single_match(url, '/(\d+P)_')
            if quality and 'validfrom=' in url:
                video_urls.append(["[pornhub] m3u %s" % quality, url])
            video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
            # logger.debug("[%s] %s" %(quality, url))
            if "get_media" in url:
                video_json = httptools.downloadpage(url, set_tls=True, set_tls_min=True).json
                for video in video_json:
                    url = video['videoUrl']
                    quality = video['quality']
                    video_urls.append(["[pornhub] mp4 %sP" % quality, url])
    
    return video_urls
