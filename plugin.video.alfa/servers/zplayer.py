# -*- coding: utf-8 -*-
# -*- Server ZPlayer -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import httptools
from core import scrapertools
from platformcode import logger
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}|\(|\)', "", data)
    if "Page not found" in data:
        return False, "[ZPlayer] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    logger.debug(data)

    video_urls = []
    patron = '"file": "([^"]+)",.*?"type": "([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for video_url, ext in matches:
        ref = scrapertools.find_single_match(video_url, '(.*?&)') + "shared=%s" % page_url
        url = video_url + "|referer=%s" % ref
        video_urls.append(["[zplayer] %s" % ext, url])

    return video_urls

