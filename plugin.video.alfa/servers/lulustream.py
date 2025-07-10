# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector lulustream By Alfa development Group
# --------------------------------------------------------
import sys

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from core import urlparse
from platformcode import logger

video_urls = []
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

host = "https://lulustream.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url, **kwargs)
    global data, server, text
    server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    data = response.data
    if not response.sucess or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False, "[lulustream] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # data = httptools.downloadpage(page_url, **kwargs).data
    try:
        # enc_data = scrapertools.find_single_match(data, "type='text/javascript'>(eval.*?)?\s+</script>")
        enc_data = scrapertools.find_multiple_matches(data, "text/javascript(?:'|\")>(eval.*?)</script>")
        dec_data = jsunpack.unpack(enc_data[-1])
    except Exception:
        dec_data = data
    # sources = 'file:"([^"]+)",label:"([^"]+)"'
    sources = 'sources\:\s*\[\{(?:file|src):"([^"]+)"'
    
    try:
        matches = re.compile(sources, re.DOTALL).findall(dec_data)
        for url in matches:
            headers = httptools.default_headers.copy()
            url += "|%s&Referer=%s/&Origin=%s" % (urlparse.urlencode(headers), host,host)
            video_urls.append(['[lulustream] m3u', url])
    except Exception:
        pass
    return video_urls
