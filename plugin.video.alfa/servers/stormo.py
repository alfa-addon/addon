# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    response = httptools.downloadpage(page_url)
    if "video_error.mp4" in response.data:
        return False, "[Stormo] El archivo no existe o ha sido borrado"
    if response.code == 451:
        return False, "[Stormo] El archivo ha sido borrado por problemas legales."

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info(" url=" + page_url)

    video_urls = []
    data = httptools.downloadpage(page_url).data
    media_url = scrapertools.find_single_match(data, "file\s*:\s*['\"]([^'\"]+)['\"]")
    if media_url.endswith("/"):
        media_url = media_url[:-1]

    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [stormo]", media_url])
    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0], video_url[1]))

    return video_urls
