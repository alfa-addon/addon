# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    video_urls = []
    videourl = scrapertools.find_single_match(data, 'source src="([^"]+)')
    video_urls.append([".MP4 [jawcloud]", videourl])

    return video_urls
