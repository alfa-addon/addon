# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Emturbovid By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import urlparse
from platformcode import logger

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)

    if "|" in page_url:
        page_url, headers = page_url.split("|")
        kwargs['headers'] = dict(urlparse.parse_qsl(headers))

    try:
        response = httptools.downloadpage(page_url, **kwargs)
    except Exception as e:
        logger.error("Error downloading page: %s" % str(e))
        return False, "[Emturbovid] Hubo un error al descargar la página"
    
    if "NameResolutionError" in str(response.code):
        return False, "[Emturbovid] El servidor DNS no ha podido resolver el dominio"
    
    if 200 != response.code:
        return False, "[Emturbovid] El servidor ha respondido con código de error: %s" % response.code
    
    data = response.data
    
    if "<b>File not found, sorry!</b" in data:
        return False, "[Emturbovid] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    server = httptools.obtain_domain(page_url)
    host = "https://%s" % server
    headers = httptools.default_headers.copy()
    headers = "|{0}&Referer={1}/&Origin={1}".format(urlparse.urlencode(headers), host)
    patron = 'data-hash\s*=\s*"([^")]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        if server not in url:
            url = urlparse.urljoin(page_url,url)
        video_urls.append(['[%s]' %server.split(".")[-2], url+headers])
    return video_urls

