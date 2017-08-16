# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "Not Found" in data:
        return False, "[streamixcloud] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    video_urls = []
    packed = scrapertools.find_single_match(data,
                                            "<script type='text/javascript'>(eval\(function\(p,a,c,k,e,d.*?)</script")
    data = jsunpack.unpack(packed)

    media_url = scrapertools.find_multiple_matches(data, '\{file:"([^"]+)",')
    # thumb = scrapertools.find_single_match(data, '\],image:"([^"]+)"')

    ext = scrapertools.get_filename_from_url(media_url[0])[-4:]

    for url in media_url:
        video_urls.append(["%s [streamixcloud]" % ext, url])

    return video_urls
