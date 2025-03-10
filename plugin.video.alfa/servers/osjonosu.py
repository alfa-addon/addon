# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector osjonosu By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, host
    host = httptools.obtain_domain(page_url, scheme=True).rstrip("/") + "/"
    kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}
    kwargs['headers'] = {'Referer': host}
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if not response.sucess or "Not Found" in data or "File was deleted" in data \
                           or "is no longer available" in data:
        return False, "[osjonosu] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)
        unpacked = unpacked.replace("\\'", "'")
        url = scrapertools.find_single_match(unpacked, "sources\:\s*\[\{'(?:file|src)':'([^']+)'")
        url = host+url
        video_urls.append(['[osjonosu] m3u8', url])
    except Exception:
        logger.error("[osjonosu] Failed to get video url.")
    return video_urls
