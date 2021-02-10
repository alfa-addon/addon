# -*- coding: utf-8 -*-
# import re
from core import httptools
from core import scrapertools
from platformcode import logger
import codecs


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    list = scrapertools.find_single_match(data, 'var urK4sa = ([^\]]+)').replace('[', '').replace('"', '').replace('\\x', '').replace(',', ' ')
    list = list.split()[::-1]
    url =""
    for elem in list:
        url += codecs.decode(elem, "hex")
    url= scrapertools.find_single_match(url, '<source src="([^"]+)"')
    video_urls.append(["[youdbox]", url])
    return video_urls

