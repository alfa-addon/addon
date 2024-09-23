# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Emturbovid By Alfa development Group
# --------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re
from core import httptools
from platformcode import logger
from lib import jsunpack
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
    if "emturbovid" in page_url:
        patron = "urlPlay\s*=\s*'([^')]+)'"
    else:
        patron = 'urlPlay\s*=\s*"([^")]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        if not server in url:
            url = urlparse.urljoin(page_url,url)
        url += "|Referer=https://%s/" %server
        video_urls.append(['[%s]' %server.split(".")[-2], url])
    return video_urls

