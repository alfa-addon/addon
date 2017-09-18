# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data:
        return False, "[bitp] El fichero ha sido borrado"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    videourl = scrapertools.find_multiple_matches(data, 'file":"([^"]+).*?label":"([^"]+)')
    scrapertools.printMatches(videourl)
    for scrapedurl, scrapedquality in videourl:
        scrapedurl = scrapedurl.replace("\\","")
        video_urls.append([scrapedquality + " [bitp]", scrapedurl])

    return video_urls
