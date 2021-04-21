# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhub By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    global data
    data = response.data
    if not response.sucess or "Not Found" in data or "Video Disabled" in data or "<div class=\"removed\">" in data or "is unavailable" in data:
        return False, "[pornhub] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    # data = httptools.downloadpage(page_url).data
    matches = scrapertools.find_single_match(data, "qualityItems_\d+ = ([^;]+)")
    for qlty in eval(matches):
        url = (qlty["url"].replace("\\", ""))
        if not url:
            continue
        quality = qlty["id"].replace("quality", "")
        video_urls.append(["%s [pornhub]" % quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

