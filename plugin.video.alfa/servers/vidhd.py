# -*- coding: utf-8 -*-
# -*- Server Vidhd -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "File Not Found" in data or "File is no longer available" in data:
        return False, "[Vidhd] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    packed = scrapertools.find_single_match(data, r"'text/javascript'>(eval.*?)\n")
    unpacked = jsunpack.unpack(packed)
    video_urls = []

    video_info = scrapertools.find_multiple_matches(unpacked, r'{(file:.*?)}')
    subtitulo = scrapertools.find_single_match(unpacked, r'tracks:\s*\[{file:"([^"]+)"')

    for info in video_info:
        
        video_url = scrapertools.find_single_match(info, r'file:"([^"]+)"')
        label = scrapertools.find_single_match(info, r'label:"([^"]+)"')
        
        if video_url == subtitulo:
            continue
        
        extension = scrapertools.get_filename_from_url(video_url)[-4:]
        
        if extension == ".mpd":
            video_urls.append(["%s %s [Vidhd]" % (extension, label), video_url, 0, subtitulo, "mpd"])
        else:
            video_urls.append(["%s %s [Vidhd]" % (extension, label), video_url, 0, subtitulo])

    return video_urls
