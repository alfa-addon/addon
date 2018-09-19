# -*- coding: utf-8 -*-

import re
import base64
import urllib

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]


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
    itemlist = []

    referer = re.sub(r"embed-|player-", "", page_url)[:-5]

    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    switch = 1 if '_0x4b94' in data else 0

    if data == "File was deleted":
        return "El archivo no existe o ha sido borrado"

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)

    url = scrapertools.find_single_match(unpacked, '(http[^,]+\.mp4)')
    itemlist.append([".mp4" + " [streamplay]", decode_video_url(url, switch)])
    itemlist.sort(key=lambda x: x[0], reverse=True)

    return itemlist

def decode_video_url(url, switch):
    tria = re.compile('[0-9a-z]{40,}', re.IGNORECASE).findall(url)[0]
    gira = tria[::-1]
    x = gira[0] + gira[2:]
    r = list(x)
    if switch == 0:
        r[4], r[2] = r[2], r[4]
        r[5], r[9] = r[9], r[5]
        r[1], r[7] = r[7], r[1]
    else:
        r[7], r[0] = r[0], r[7]
        r[3], r[6] = r[6], r[3]
        r[2], r[5] = r[5], r[2]
    return re.sub(tria, ''.join(r), url)
