# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mangovideo By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger

server = {'1': 'https://www.mangovideo.pw/contents/videos/', '7' : 'https://server9.mangovideo.pw/contents/videos/',
          '8' : 'https://s10.mangovideo.pw/contents/videos/', '9' : 'https://server2.mangovideo.pw/contents/videos/',
          '10' : 'https://server217.mangovideo.pw/contents/videos/', '11' : 'https://234.mangovideo.pw/contents/videos/',
          '12' : 'https://98.mangovideo.pw/contents/videos/'
         }


def test_video_exists(page_url):

    response = httptools.downloadpage(page_url)

    if not response.sucess or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "is no longer available" in response.data:
        return False, "[mangovideo] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    video_urls = []
    if "embed" in page_url:
        data = httptools.downloadpage(page_url)
        page_url= scrapertools.find_single_match(data, '/(https://mangovideo.pw/get_file/.*?.mp4)/')
    scrapedurl= scrapertools.find_single_match(page_url, 'https://mangovideo.pw/get_file/\d+/.*?/([^"]+)')
    scrapedserver = scrapertools.find_single_match(page_url, 'https://mangovideo.pw/get_file/(\d+)')
    scrapedserver = server.get(scrapedserver, scrapedserver)
    url = scrapedserver + scrapedurl
    video_urls.append(["[mangovideo]", url])
    return video_urls