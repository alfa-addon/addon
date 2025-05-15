# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url, **kwargs).data
    if "This video is no longer available" in data or 'no está disponible' in data:
        return False, "[spankbang] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    if "embed" in page_url:
        page_url = scrapertools.find_single_match(data,'<link rel="canonical" href="([^"]+)"')
    data = httptools.downloadpage(page_url, **kwargs).data
    data = scrapertools.find_single_match(data,'stream_data\s+=\s+([^\}]+)')
    
    
    # url = scrapertools.find_single_match(data,'<source src="(.*?)"')
    # video_urls.append(['[.mp4]', url])
    # if "embed" in page_url:
        # page_url = scrapertools.find_single_match(data,'<link rel="canonical" href="([^"]+)"')
    # skey = scrapertools.find_single_match(data,'data-streamkey="([^"]+)"')
    # #session="523034c1c1fc14aabde7335e4f9d9006b0b1e4984bf919d1381316adef299d1e"
    # post = {"id": skey, "data": 0}
    # headers = {'Referer': page_url}
    # url = "https://spankbang.com/api/videos/stream_embed"
    # data = httptools.downloadpage(url, post=post, headers=headers, **kwargs).data
    # patron = '"(\d+(?:p|k))":\["([^"]+)"'
    
    patron = "'(\d+p)': \['([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        if "4k" in quality:
            quality = "2160p"
        video_urls.append(['[spankbang] %s' %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

