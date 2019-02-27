# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector anonfile By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[anonfile] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron = 'id="download-quality-(\w+).*?href="([^"]+)"'
    match = scrapertools.find_multiple_matches(data, patron)
    for calidad, media_url in match:
        title = "%s [anonfile]" % (calidad)
        video_urls.append([title, media_url, int(calidad.replace("p", ""))])

    video_urls.sort(key=lambda x: x[2])
    for video_url in video_urls:
        video_url[2] = 0
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
