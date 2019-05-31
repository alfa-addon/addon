# -*- coding: utf-8 -*-

import re
import base64
import urllib

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    if data == "File was deleted":
        return False, "[Streamplay] El archivo no existe o ha sido borrado"
    elif "Video is processing now" in data:
        return False, "[Streamplay] El archivo se está procesando"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    video_urls = []

    referer = re.sub(r"embed-|player-", "", page_url)[:-5]

    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    if data == "File was deleted":
        return "El archivo no existe o ha sido borrado"

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)

    sources = eval(scrapertools.find_single_match(unpacked, "sources=(\[[^\]]+\])"))
    for video_url in sources:
        
        from lib import alfaresolver
        video_url = alfaresolver.decode_video_url(video_url, data)
        filename = scrapertools.get_filename_from_url(video_url)[-4:]
        if not video_url.endswith(".mpd"):
            video_urls.append([filename + " [streamplay]", video_url])

    video_urls.sort(key=lambda x: x[0], reverse=True)

    return video_urls