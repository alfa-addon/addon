# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector lauchacohete By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    referer = "https://www.pelis182.com/"
    global data
    kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}
    kwargs['headers'] = {'Referer': referer}
    response = httptools.downloadpage(page_url, **kwargs)
    if not response or not response.sucess or "404 - NOT FOUND!" in response.data:
        return False, "[lauchacohete] El fichero no existe o ha sido borrado"
    
    data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    referer = "https://lauchacohete.top/"
    headers = "|Referer=%s" % referer
    global data
    video_urls = []
    try:
        video = scrapertools.find_single_match(data, r'sources:\s+\[\{"file":"([^"]+)')
        if video and video.endswith(".m3u8"):
            subtitle = scrapertools.find_single_match(data, r'tracks:\s+\[\{"file":"([^"]+)')
            if subtitle and subtitle.endswith(".srt"):
                video_urls.append(['[lauchacohete] m3u8', video+headers, 0, subtitle+headers])
            else:
                video_urls.append(['[lauchacohete] m3u8', video+headers])
    except Exception:
        logger.error("[lauchacohete] Failed to get video url.")
    return video_urls