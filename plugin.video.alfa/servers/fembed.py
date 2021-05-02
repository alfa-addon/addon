# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Fembed By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    id = scrapertools.find_single_match("v/(\w+)", page_url)
    post = "r=&d=feurl.com"
    data = httptools.downloadpage(page_url, post=post).json
    if not data.get('success', ''):
        return False, "[Fembed] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    for url in data["data"]:
        video_urls.append([url["label"] + " [Fembed]", url["file"]])
    return video_urls
