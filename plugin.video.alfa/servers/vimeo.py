# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    headers = [['User-Agent', 'Mozilla/5.0']]
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        headers.append(['Referer', referer])
    if not page_url.endswith("/config"):
        page_url = scrapertools.find_single_match(page_url, ".*?video/[0-9]+")

    data = httptools.downloadpage(page_url, headers=headers).data
    patron = 'mime":"([^"]+)"'
    patron += '.*?url":"([^"]+)"'
    patron += '.*?quality":"([^"]+)"'
    match = scrapertools.find_multiple_matches(data, patron)
    for mime, media_url, calidad in match:
        title = "%s (%s) [vimeo]" % (mime.replace("video/", "."), calidad)
        video_urls.append([title, media_url, int(calidad.replace("p", ""))])

    video_urls.sort(key=lambda x: x[2])
    for video_url in video_urls:
        video_url[2] = 0
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
