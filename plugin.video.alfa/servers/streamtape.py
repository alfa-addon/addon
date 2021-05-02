# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamtape By Alfa development Group
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
    global data

    referer = {"Referer": page_url}

    data = httptools.downloadpage(page_url, headers=referer).data
    if "Video not found" in data:
        return False, "[streamtape] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    url = "https:" + eval(scrapertools.find_single_match(data, "innerHTML = ([^;]+)"))
    video_urls.append(['MP4 [streamtape]', url + "|User-Agent=%s" % httptools.get_user_agent()])
    return video_urls
