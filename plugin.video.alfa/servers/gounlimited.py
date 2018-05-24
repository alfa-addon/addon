# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector GoUnlimited By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from platformcode import logger
from core import scrapertools
from lib import jsunpack


def test_video_exists(page_url):
    data = httptools.downloadpage(page_url).data
    if data == "File was deleted":
        return False, "[gounlimited] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed_data)
    patron = "file:(.*?),label:(.*?)}"
    matches = re.compile(patron, re.DOTALL).findall(unpacked)
    for url, quality in matches:
        video_urls.append(['%s' % quality, url])
    video_urls.sort(key=lambda x: int(x[0]))
    return video_urls
