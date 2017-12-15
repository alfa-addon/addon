# -*- coding: utf-8 -*-
import time

from core import httptools
from core import scrapertools
from platformcode import logger

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Archive no Encontrado" in data:
        return False, "[bdupload] El fichero ha sido borrado"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    post = ""
    patron = '(?s)type="hidden" name="([^"]+)".*?value="([^"]*)"'
    match = scrapertools.find_multiple_matches(data, patron)
    for nombre, valor in match:
        post += nombre + "=" + valor + "&"
    time.sleep(1)
    data1 = httptools.downloadpage(page_url, post = post, headers = headers).data
    patron = "window.open\('([^']+)"
    file = scrapertools.find_single_match(data1, patron)
    file += "|User-Agent=" + headers['User-Agent']
    video_urls = []
    videourl = file
    video_urls.append([".MP4 [bdupload]", videourl])
    return video_urls
