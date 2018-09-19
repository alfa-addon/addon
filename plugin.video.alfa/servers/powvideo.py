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
    referer = page_url.replace('iframe', 'preview')
    data = httptools.downloadpage(page_url, headers={'referer': referer}).data
    if data == "File was deleted" or data == '':
        return False, "[powvideo] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    referer = page_url.replace('iframe', 'preview')

    data = httptools.downloadpage(page_url, headers={'referer': referer}).data
    switch = 0 if '_0x4a3f' in data else 1 if '_0x34ab' in data else 2 if '_0x5db1' in data else 3 

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)
    
    url = scrapertools.find_single_match(unpacked, "(?:src):\\\\'([^\\\\]+.mp4)\\\\'")

    itemlist.append([".mp4" + " [powvideo]", decode_video_url(url, switch)])
    itemlist.sort(key=lambda x: x[0], reverse=True)
    return itemlist

def decode_video_url(url, switch):
    tria = re.compile('[0-9a-z]{40,}', re.IGNORECASE).findall(url)[0]
    gira = tria[::-1]
    x = gira[0] + gira[2:]
    r = list(x)
    if switch == 0:
        r[7], r[4] = r[4], r[7]
        r[0], r[9] = r[9], r[0]
        r[3], r[2] = r[2], r[3]
    elif switch == 1:
        r[5], r[0] = r[0], r[5]
        r[3], r[6] = r[6], r[3]
        r[8], r[9] = r[9], r[8]
    elif switch == 2:
        r[9], r[3] = r[3], r[9]
        r[6], r[1] = r[1], r[6]
        r[0], r[7] = r[7], r[0]
    return re.sub(tria, ''.join(r), url)
