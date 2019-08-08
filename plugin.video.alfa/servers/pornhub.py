# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhub By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    response = httptools.downloadpage(page_url)
    if not response.sucess or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "removed" in response.data \
       or not "defaultQuality" in response.data \
       or "is no longer available" in response.data:
        return False, "[pornhub] El fichero no existe o ha sido borrado"
    return True, ""

def get_video_url(page_url, user="", password="", video_password=""):
    logger.info()
    video_urls = []
    data = httptools.downloadpage(page_url).data
    videourl = scrapertools.find_multiple_matches(data, '"format":"mp4","quality":"(\d+)","videoUrl":"(.*?)"')
    scrapertools.printMatches(videourl)
    for scrapedquality,scrapedurl in videourl:
        scrapedurl = scrapedurl.replace("\\","")
        video_urls.append([scrapedquality + "p [pornhub]", scrapedurl])
    return video_urls

