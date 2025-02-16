# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidhide By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools, jsontools
from core import scrapertools
from platformcode import logger
from lib import jsunpack

video_urls = []

# forced_proxy_opt = 'ProxySSL'
# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    if "|Referer" in page_url or "|referer" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {'Referer': referer}
    response = httptools.downloadpage(page_url, **kwargs)
    global data
    data = response.data
    if not response.sucess or "Not Found" in data or "File was deleted" in data \
                           or "is no longer available" in data:
        return False, "[vidhide] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    try:
        enc_data = scrapertools.find_single_match(data, "text/javascript(?:'|\")>(eval.*?)</script>")
        dec_data = jsunpack.unpack(enc_data)
        url = scrapertools.find_single_match(dec_data, 'sources\:\s*\[\{(?:file|src):"([^"]+)"')
        video_urls.append(['[vidhide] m3u', url])
    except Exception:
        dec_data = data
    return video_urls
