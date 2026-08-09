# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger
from bs4 import BeautifulSoup


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    page = page_url.split('/video/')
    host = page[0]
    id = page[-1]
    post_url = "%s/api/video-info" %host
    post = {'videoId': id}
    data = httptools.downloadpage(post_url, post=post).json
    
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[HogTV] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    for elem in data['playerData']['sources']:
        url = elem['src']
        quality = elem['quality']
        if not url.startswith("https"):
            url = "https:%s" % url
        video_urls.append(["[HogTV] %s" %quality, url])
    return video_urls[::-1]

