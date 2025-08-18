# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import random
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse

if not PY3: from lib import alfaresolver
else: from lib import alfaresolver_py3 as alfaresolver


kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'ignore_response_code': True, 'cf_assistant': False}

host = "https://goodstream.one" 

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url, **kwargs).data
    if "<h2>WE ARE SORRY</h2>" in data or 'No such file' in data:
        return False, "[GoodStream] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    url = scrapertools.find_single_match(data, 'file:\s*"([^"]+)"')
    # url += "|Referer=%s" % page_url
    headers = httptools.default_headers.copy() 
    url += "|%s&Referer=%s/&Origin=%s" % (urlparse.urlencode(headers), host,host)
    
    video_urls.append(["[GoodStream] m3u", url])
    return video_urls

