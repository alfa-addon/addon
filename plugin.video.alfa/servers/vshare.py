# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    if httptools.downloadpage(page_url).code != 200:
        return False, "El archivo no existe en vShare o ha sido borrado."
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url = " + page_url)

    data = httptools.downloadpage(page_url).data

    flowplayer = re.search("url: [\"']([^\"']+)", data)
    if flowplayer:
        return [["FLV", flowplayer.group(1)]]

    jsUnpack = jsunpack.unpack(data)
    logger.debug(jsUnpack)

    video_urls = []

    fields = re.search("\[([^\]]+).*?parseInt\(value\)-(\d+)", jsUnpack)
    if fields:
        logger.debug("Values: " + fields.group(1))
        logger.debug("Substract: " + fields.group(2))
        substract = int(fields.group(2))

        arrayResult = [chr(int(value) - substract) for value in fields.group(1).split(",")]
        strResult = "".join(arrayResult)
        logger.debug(strResult)
        videoSources = re.findall("<source[\s]+src=[\"'](?P<url>[^\"']+)[^>]+label=[\"'](?P<label>[^\"']+)", strResult)
        for url, label in videoSources:
            video_urls.append([label, url])
    video_urls.sort(key=lambda i: int(i[0].replace("p","")))
    return video_urls
