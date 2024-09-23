# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from lib import jsunhunt
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    response = httptools.downloadpage(page_url)
    data = response.data
    server = scrapertools.find_single_match(page_url, '//(?:www.|es.|)([A-z0-9-]+).(?:co|net)')
    if ">404</h1>" in data or '<title>404' in data or response.code == 404:
        return False, "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url, headers={'Referer': page_url}).data
    if jsunhunt.detect(data):
        data = jsunhunt.unhunt(data)
        url = scrapertools.find_single_match(data, 'urlPlay\s*=\s*"([^")]+)"').strip()
        url += "|Referer=%s" % page_url
        video_urls.append(["[%s]" %server, url])
    return video_urls

