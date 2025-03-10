# Conector bigwarp By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'ignore_response_code': True, 'cf_assistant': False, 'timeout': 20}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "not found" in response.data:
        return False,  "[bigwarp] El fichero no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        sources = 'sources\:\s*\[\{(?:file|src):"([^"]+)"'
        matches = re.compile(sources, re.DOTALL).findall(data)
        for url in matches:
            url += "|Referer=%s" %page_url
            video_urls.append(['[bigwarp] mp4', url])
    except Exception:
        logger.debug(data)
    return video_urls
