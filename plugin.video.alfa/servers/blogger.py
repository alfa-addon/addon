# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Blogger By Alfa development Group
# --------------------------------------------------------
import re
import codecs
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data

    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if data.code == 404:
        return False, "[blogger] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    logger.debug(data)
    streams = scrapertools.find_single_match(data, r'"streams":(\[.*?\])')
    logger.debug(streams)

    if streams:
        streams = eval(streams)
    for strm in streams:
        url = codecs.decode(strm["play_url"],"unicode-escape")
        video_urls.append(['Directo [Blogger]', url])

    return video_urls
