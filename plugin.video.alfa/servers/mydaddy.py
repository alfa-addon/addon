# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mydaddy By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host = 'https://mydaddy.cc' #'https://myxstudio.top'

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
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data 
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if response.code == 404 or "Not Found" in data \
       or "File was deleted" in data \
       or "is no longer available" in data:
        return False, "[mydaddy] El fichero no existe o ha sido borrado"
    if "This domain has been blocked" in data:
        return False, "[mydaddy] This domain has been blocked"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data 
    
    data = data.replace("\\", "")
    matches = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" title="(\d+p)')
    for url,quality in matches:
        if not url.startswith("https"):
            url = "https:%s" % url
        url += "|Referer=%s/&Origin=%s" % (host, host)
        video_urls.append(["[mydaddy] %s" % quality, url])
    return video_urls

