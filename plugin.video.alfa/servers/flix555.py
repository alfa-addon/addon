# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from lib import jsunpack
from platformcode import logger

data = ""
def test_video_exists(page_url):
    resp = httptools.downloadpage(page_url)
    global data
    data = resp.data
    if resp.code == 404 or '<b>File Not Found</b>' in resp.data or "<b>File is no longer available" in resp.data:
        return False, "[flix555] El video no está disponible"
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)
    # ~ logger.info(unpacked)

    matches = scrapertools.find_multiple_matches(unpacked, 'file\s*:\s*"([^"]*)"\s*,\s*label\s*:\s*"([^"]*)"')
    if matches:
        for url, lbl in matches:
            if not url.endswith('.srt'):
                itemlist.append(['.mp4 (%s) [flix555]' % lbl, url])

    return itemlist

