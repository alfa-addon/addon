# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector wolfstream By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import scrapertools
from platformcode import logger
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    data = httptools.downloadpage(page_url)
    server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    if data.code == 404 or "no longer available" in data.data:
        return False, "[wolfstream] El archivo no existe o ha sido borrado"
    data = data.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    m3u8_source = scrapertools.find_single_match(data, '\{file:"([^"]+)"\}')
    video_urls.append(['[%s] m3u8' %server, m3u8_source])
    return video_urls

