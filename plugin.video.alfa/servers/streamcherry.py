# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector para streamcherry
# --------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "We are unable to find the video" in data:
        return False, "[streamcherry] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    video_urls = []
    matches = scrapertools.find_multiple_matches(data, 'type\s*:\s*"([^"]+)"\s*,\s*src:"([^"]+)",height\s*:\s*(\d+)')
    for ext, media_url, calidad in matches:
        ext = ext.replace("video/", "")
        if not media_url.startswith("http"):
            media_url = "http:%s" % media_url
        video_urls.append([".%s %sp [streamcherry]" % (ext, calidad), media_url])

    video_urls.reverse()
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls


# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    patronvideos = 'streamcherry.com/(?:embed|f)/([A-z0-9]+)'
    logger.info("#" + patronvideos + "#")
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for match in matches:
        titulo = "[streamcherry]"
        url = "http://streamcherry.com/embed/%s" % match
        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'streamcherry'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)

    return devuelve
