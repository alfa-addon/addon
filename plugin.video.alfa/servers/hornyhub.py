# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

kwargs = {
    "set_tls": None,
    "set_tls_min": False,
    "retries_cloudflare": 1,
    "ignore_response_code": True,
    "cf_assistant": False,
}

host = "https://zhornyhub.com/"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    data = httptools.downloadpage(page_url, **kwargs).data
    
    if data == "File was deleted" or data == '':
        return False, "[hornyhub] El video ha sido borrado"


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    txt = scrapertools.find_single_match(data, "var jw = (\{.*?);")
    patron ='"type":"mp4","label":"([^"]+)","file":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(txt, patron)
    
    for quality, url in matches:
        url = url.replace("\/", "/")
        video_urls.append(["[hornyhub] %s" %quality, url])
    return video_urls
