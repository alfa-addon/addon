# -*- coding: utf-8 -*-

import urllib

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data:
        return False, "[Vidup] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    post= {}
    post = urllib.urlencode(post)
    url = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers.get("location", "")
    data = httptools.downloadpage("https://vidup.io/api/serve/video/" + scrapertools.find_single_match(url, "embed/([A-z0-9]+)"), post=post).data
    bloque = scrapertools.find_single_match(data, 'qualities":\{(.*?)\}')
    matches = scrapertools.find_multiple_matches(bloque, '"([^"]+)":"([^"]+)')
    for res, media_url in matches:
        video_urls.append(
            [scrapertools.get_filename_from_url(media_url)[-4:] + " (" + res + ") [vidup.tv]", media_url])
    video_urls.reverse()
    return video_urls
