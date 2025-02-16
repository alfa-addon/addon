# Conector tiwikiwi By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}


# https://filemooon.link/e/mlx76kltz6tn    


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    
    datos = httptools.downloadpage(page_url, **kwargs).data
    if "not found" in datos:
        return False,  "[filemoon] El fichero no existe o ha sido borrado"
    else:
        page_url = scrapertools.find_single_match(datos, '<iframe src="([^"]+)')
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "not found" in response.data:
        return False,  "[filemoon] El fichero no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
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
            video_urls.append(['[filemoon] m3u', url])
    except Exception:
        pass
    return video_urls
