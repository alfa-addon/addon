# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Conector para cloudsany
# https://github.com/alfa-addon
# ------------------------------------------------------------

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data:
        return False, "[Cloudsany] El fichero ha sido borrado"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    data = scrapertools.find_single_match(data, 'p,a,c,k,e.*?</script>')
    unpack = jsunpack.unpack(data)
    logger.info("Intel11 %s" %unpack)
    video_urls = []
    videourl = scrapertools.find_single_match(unpack, 'config={file:"([^"]+)')
    video_urls.append([".MP4 [Cloudsany]", videourl])

    return video_urls
