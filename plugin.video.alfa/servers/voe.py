# -*- coding: utf-8 -*-
# -*- Server Voe -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools
from core import scrapertools
from core.jsontools import json
from platformcode import logger
import sys
import base64

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "Not found" in data or "File is no longer available" in data or "Error 404" in data:
        return False, "[Voe] El fichero no existe o ha sido borrado"

    if "permanentToken" in data:
        match = scrapertools.find_single_match(data, "(?i)window\.location\.href\s*=\s*'([^']+)'")
        data = httptools.downloadpage(match).data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    video_srcs = scrapertools.find_multiple_matches(data, r"(?:mp4|hls)': '([^']+)'")
    if not video_srcs:
        bloque = scrapertools.find_single_match(data, "sources.*?\}")
        video_srcs = scrapertools.find_multiple_matches(bloque, ": '([^']+)")
        
    if video_srcs:
        for url in video_srcs:
            if url.startswith("aHR0"):
                url = base64.b64decode(url).decode("utf-8")
            video_urls.append([" [Voe]", url])
    else:
        try:
            match = scrapertools.find_single_match(data, "(?i)let\s[0-9a-f]+\s=\s'(.*?)'")
            dec_string = base64.b64decode(match).decode("utf-8")
            data_json = json.loads(dec_string[::-1])
            video_urls.append([" [Voe]", data_json['file']])
        except Exception as error:
            logger.error("Exception: {}".format(error))

    return video_urls
