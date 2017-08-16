# -*- coding: utf-8 -*-

from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)
    if ("File was deleted" or "Not Found") in data: return False, "[Streame] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    data = scrapertools.cache_page(page_url)
    media_urls = scrapertools.find_multiple_matches(data, '\{file:"([^"]+)",label:"([^"]+)"\}')
    video_urls = []
    for media_url, label in media_urls:
        video_urls.append(
            [scrapertools.get_filename_from_url(media_url)[-4:] + " (" + label + ") [streame]", media_url])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
