# -*- coding: utf-8 -*-

from aadecode import decode as aadecode
from core import scrapertools
from core import httptools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "This video doesn't exist." in data:
        return False, '[videowood] El video no puede ser encontrado o ha sido eliminado.'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    text_encode = scrapertools.find_single_match(data, "(eval\(function\(p,a,c,k,e,d.*?)</script>")
    text_decode = aadecode(text_encode)
    patron = "'([^']+)'"
    media_url = scrapertools.find_single_match(text_decode, patron)
    video_urls.append([media_url[-4:] + " [Videowood]", media_url])
    return video_urls
