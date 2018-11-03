# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Conector para xdrive
# https://github.com/alfa-addon
# ------------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Object not found" in data or "no longer exists" in data or '"sources": [false]' in data:
        return False, "[xdrive] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data

    from urllib2 import urlopen
    my_ip = urlopen('http://ip.42.pl/raw').read()

    videolink = scrapertools.find_single_match(data, r"response.data.ip;\s*axios.get.'(.*?)'\)")
    videolink = videolink.replace("'+ip_adress+'", my_ip)
    data = httptools.downloadpage(videolink).data
    videourl = scrapertools.find_multiple_matches(data, '"(.*?)"')

    for scrapedurl in videourl:
        scrapedurl = scrapedurl.replace("\\", "")
        if '.mp4' not in scrapedurl: continue
        video_urls.append([ " [xdrive]", scrapedurl])
    return video_urls
