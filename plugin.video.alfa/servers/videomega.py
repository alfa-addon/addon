# -*- coding: utf-8 -*-
from core import urlparse as alfa_urlparse
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    m= scrapertools.find_single_match(data, '<link href="(Br74.*?==.css)"')
    n= scrapertools.find_single_match(data, '<link href="(JaV.*?.css)"')
    url= alfa_urlparse.build_url('https://www.videomega.co', u'/streamurl/{}.css/'.format(n))
    post="myreason=%s&saveme=/videojs/crexcode/video-js.min.css" %m
    url = httptools.downloadpage(url, post=post).data
    url = url.replace(" ", "")
    data=httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    video_urls.append(["[videomega]", url])
    return video_urls

