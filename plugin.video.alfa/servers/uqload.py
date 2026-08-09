# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Uqload By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack


kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 1, #'forced_proxy_ifnot_assistant': forced_proxy_opt,
          'ignore_response_code': True, 'cf_assistant': False, 'CF_stat': True, 'CF': True,
          'timeout': 15}

host= "https://uqload.is"


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    kwargs['headers'] = {
                         'Referer': '%s/' %host,
                         'Origin': host,
                         # 'Content-Type': 'application/json;charset=UTF-8',
                         # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                         # 'Sec-Fetch-Dest': 'empty',
                         # 'Sec-Fetch-Mode': 'cors',
                         # 'Sec-Fetch-Site': 'same-site',
                         # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                        }
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or 'File was deleted' in data:
        return False, "[Uqload] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    packed = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
    unpacked = jsunpack.unpack(packed)
    patron = 'sources:\[\{file:"([^"]+)"'
    url = scrapertools.find_single_match(unpacked, patron)
    url += '|Referer=%s' %host
    video_urls.append(["[uqload]", url])
    return video_urls
