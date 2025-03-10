# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Vudeo By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url)
    if data.code != 200 or 'File was deleted' in data.data:
        return False, "[Vudeo] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    patron = 'sources:.?\["([^"]+)"\]'
    matches = scrapertools.find_multiple_matches(data.data, patron)
    domain = httptools.obtain_domain(page_url, scheme=True)
    for url in matches:
        url = '{}|Referer={}/'.format(url, domain)
        video_urls.append(["[vudeo]", url])
    return video_urls
