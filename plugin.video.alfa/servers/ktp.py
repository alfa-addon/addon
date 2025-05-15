# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vipporns By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger

from lib.kt_player import decode

# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'ignore_response_code': True, 'cf_assistant': False}
# kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 3, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

# https://trahkino.cc/video/353484/ necesita "False"
# https://www.porn00.org/ necesita "None"

def test_video_exists(page_url):
    
    response = httptools.downloadpage(page_url, **kwargs)
    if response.code == 404 \
    or "cwtvembeds" in page_url \
    or "Page not Found" in response.data \
    or "File was deleted" in response.data \
    or "not allowed to watch this video" in response.data \
    or "video is a private" in response.data \
    or "is no longer available" in response.data\
    or "Embed Player Error" in response.data:
        return False, "[ktplayer] El fichero no existe o ha sido borrado"
    
    global data, license_code
    data = response.data
    license_code = scrapertools.find_single_match(response.data, 'license_code:\s*(?:\'|")([^\,]+)(?:\'|")')
    
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    invert = ""
    url = ""
    data = httptools.downloadpage(page_url, **kwargs).data
    if "flashvars.video_url_text" in data: #sunporno
        data = scrapertools.find_single_match(data, '(flashvars.video_url[^\}]+)')
        patron = "(?:flashvars.video_url|flashvars.video_alt_url)\s*=\s*'([^']+)'.*?"
        patron += "(?:flashvars.video_url_text|flashvars.video_alt_url_text)\s*=\s*'([^']+)'"
    elif "video_url_text" in data:
        patron = '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += '(?:video_url_text|video_alt_url_text|video_alt_url[0-9]*_text):\s*(?:\'|")([^\,]+)(?:\'|")'
    else:
        patron = 'video_url:\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += 'postfix:\s*(?:\'|")([^\,]+)(?:\'|")'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, quality in matches:
        if "?login" not in url and "signup" not in url and "_preview" not in url and ".mp4" in url:
            if "function/" in url:
                url = decode(url, license_code)
            elif url.startswith("/get_file/"):
                url = urlparse.urljoin(page_url, url)
            if "HD" in quality and not "Full" in quality:
                quality = "720p"
            if "?br=" in url: url = url.split("?br=")[0]
            # url += "|verifypeer=false"
            url += "|Referer=%s" % page_url
            video_urls.append(['[ktplayer] %s' % quality, url])
        
        if "lq" in quality.lower() or "high" in quality.lower() or "low" in quality.lower():
            invert= "true"
        elif "mq" in quality.lower() or "hq" in quality.lower() or "full" in quality.lower(): ### 4kporn
            invert= "false"
    
    if "true" in invert:
        video_urls.reverse()
    elif "false" in invert:
        return video_urls
    else:
        video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    
    if not url:
        url = scrapertools.find_single_match(data, '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?')
        video_urls.append(['[ktplayer]', url])
    return video_urls

