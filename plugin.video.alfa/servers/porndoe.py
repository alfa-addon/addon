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
        return False, "[porndoe] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    id = scrapertools.find_single_match(data, '"id": "(\d+)"')
    post = "https://porndoe.com/service/index?device=desktop&page=video&id=%s" %id
    headers = {"Referer": page_url}
    data = httptools.downloadpage(post, headers=headers).json
    matches = data['payload']['player']['sources']['mp4']
    for elem in matches:
        url = elem['link']
        if "signup" in url:
            continue
        quality = elem['height']
        video_urls.append(['%sp' %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls

