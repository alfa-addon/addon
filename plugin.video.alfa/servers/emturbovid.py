# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Emturbovid By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import urlparse
from platformcode import logger
from core import scrapertools

# forced_proxy_opt = 'ProxySSL'
# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


def test_video_exists(page_url):
    global data, server
    logger.info("(page_url='%s')" % page_url)
    if "|Referer" in page_url or "|referer" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {'Referer': referer}
    response = httptools.downloadpage(page_url, **kwargs)
    
    data = response.data
    server = scrapertools.get_domain_from_url(page_url)
    if "<b>File not found, sorry!</b" in data:
        return False, "[Emturbovid] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    # if "emturbovid" in page_url:
        # patron = "urlPlay\s*=\s*'([^')]+)'"
    # else:
        # patron = 'urlPlay\s*=\s*"([^")]+)"'
    patron = 'data-hash\s*=\s*"([^")]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        if server not in url:
            url = urlparse.urljoin(page_url,url)
        url += "|Referer=https://%s/" %server
        video_urls.append(['[%s]' %server.split(".")[-2], url])
    return video_urls

