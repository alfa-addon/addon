# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector dropbox By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import scrapertools
from platformcode import logger
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url, only_headers=True).headers
    if data.code == 404:
        return False, "[dropbox] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    # if not "torrent" in page_url:
    video_urls.append(['MP4 [dropbox]', page_url])
    return video_urls

