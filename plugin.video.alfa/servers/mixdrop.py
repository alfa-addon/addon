# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Mixdrop By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    if "/f/" in page_url:
        page_url = page_url.replace("/f/", "/e/")
    data = httptools.downloadpage(page_url).data
    if ">WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, config.get_localized_string(70449) % "MixDrop"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    ext = '.mp4'
    
    packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)
    # mixdrop like to change var name very often, hoping that will catch every
    list_vars = scrapertools.find_multiple_matches(unpacked, r'MDCore\.\w+\s*=\s*"([^"]+)"')
    logger.debug(list_vars)
    for var in list_vars:
        if '.mp4' in var:
            media_url = var
            break
    else:
        media_url = ''

    if not media_url.startswith('http'):
        media_url = 'https:%s' % media_url
    
    media_url += "|User-Agent=%s&Referer=%s" % (httptools.get_user_agent(), page_url)
    
    video_urls.append(["[Mixdrop] %s" % ext, media_url])
    
    return video_urls
