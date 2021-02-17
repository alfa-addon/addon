# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    
    data = httptools.downloadpage(page_url).data
    if "Lo sentimos" in data or "File not found" in data or 'og:video">' in data:
        return False, "[Xvideos] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    m3u = scrapertools.find_single_match(data, 'html5player.setVideoHLS\(\'([^\']+)\'')
    data = httptools.downloadpage(m3u).data
    patron = 'RESOLUTION=\d+x(\d+),.*?'
    patron += '(hls-.*?.m3u8)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        url = m3u.replace("hls.m3u8", url)
        video_urls.append(['%sp' %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls
