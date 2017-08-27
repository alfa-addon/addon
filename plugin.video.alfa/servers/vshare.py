# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "File was deleted" in data:
        return False, "El archivo no existe<br/>en streaminto o ha sido borrado."
    elif "Video is processing now" in data:
        return False, "El archivo está siendo procesado<br/>Prueba dentro de un rato."
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
            logger.debug("[" + label + "] " + url)
            video_urls.append([label, url])

    return video_urls
