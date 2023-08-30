# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector rumble By Alfa development Group
# --------------------------------------------------------
import re
from core import jsontools
from core import httptools
from core import scrapertools
from platformcode import logger
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, "[rumble] El archivo no existe o ha sido borrado"
    data = data.data
    embed_url = scrapertools.find_single_match(data, 'embedUrl":"([^"]+)')
    logger.info("(embed_url='%s')" % embed_url)
    data = httptools.downloadpage(embed_url)
    if data.code == 404:
        return False, "[rumble] El archivo no existe o ha sido borrado"
    data = data.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []

    # los datos que salen no son realmente json, es javascript
    json_raw = scrapertools.find_single_match(data, r'"\]=(\{[^;]+)')
    # pero haciendo una pequeña limpieza se pueden hacer pasar por json
    json_split = json_raw.split(':')
    json_split[-1] = 'null}'
    del json_split[-2]
    json_fixed = ":".join(json_split)
    # una vez limpios ya se pueden cargar como un objeto json que podemos leer mejor
    json_data = jsontools.load(json_fixed)

    qualities = []
    for elem in json_data['ua']['mp4']:
        qualities.append(elem)

    qualities.sort(reverse=True)

    for quality in qualities:
        video_urls.append(['%s [rumble]' % quality, json_data['ua']['mp4'][quality]['url']])
        # logger.info("RUMBLE %s: %s" % (quality, json_data['ua']['mp4'][quality]['url']), True)

    return video_urls
