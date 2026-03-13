# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[definebabe] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    res = ['480', '720']
    for quality in res:
        url = "https://www.definebabe.com/player/get_video.php?q=%sp" %quality
        response = httptools.downloadpage(url, follow_redirects=False, referer=page_url)
        redir = response.headers.get("location", '')
        video_urls.append(["[definebabe] %s" %quality, redir])
    return video_urls

