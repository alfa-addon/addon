# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Badshare By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global page
    page = httptools.downloadpage(page_url)
    if not page.sucess:
        return False, "[Badshare] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    ext = '.mp4'

    data = page.data
    data =  re.sub(r'\n|\r|\t|\s{2,}', "", data)
    media_url, ext = scrapertools.find_single_match(data, r'file:\s*"([^"]+)",type:\s*"([^"]+)"')
    
    video_urls.append(["%s [Badshare]" % ext, media_url])

    return video_urls
