# -*- coding: utf-8 -*-

import sys
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    
    response = httptools.downloadpage(page_url)
    data = response.data
    
    if response.code == 404 or "Not Found" in data or "no longer available" in data:
        return False,  "[turboviplay] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    global data
    
    url = scrapertools.find_single_match(data, "var urlPlay = '([^']+)'")
    
    video_urls.append(['[turboviplay] m3u', url])
    return video_urls

