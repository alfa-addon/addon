# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]
host = "http://streamplay.to/"


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
    logger.info("(page_url='%s')" % page_url)
    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data

    matches = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    data = jsunpack.unpack(matches).replace("\\", "")

    data = scrapertools.find_single_match(data.replace('"', "'"), "sources\s*=[^\[]*\[([^\]]+)\]")
    matches = scrapertools.find_multiple_matches(data, "[src|file]:'([^']+)'")
    if len(matches) == 0:
        matches = scrapertools.find_multiple_matches(data, "[^',]+")
    video_urls = []
    for video_url in matches:
        if video_url.endswith(".mpd"):
            continue
        _hash = scrapertools.find_single_match(video_url, '[A-z0-9\_\-]{40,}')
        hash = _hash[::-1]
        hash = hash.replace(hash[1:2], "", 1)
        video_url = video_url.replace(_hash, hash)

        filename = scrapertools.get_filename_from_url(video_url)[-4:]
        if video_url.startswith("rtmp"):
            rtmp, playpath = video_url.split("vod/", 1)
            video_url = "%svod/ playpath=%s swfUrl=%splayer6/jwplayer.flash.swf pageUrl=%s" % \
                        (rtmp, playpath, host, page_url)
            filename = "RTMP"
        elif video_url.endswith("/v.mp4"):
            video_url_flv = re.sub(r'/v.mp4', '/v.flv', video_url)
            video_urls.append(["flv [streamplay]", video_url_flv])

        video_urls.append([filename + " [streamplay]", video_url])

    video_urls.sort(key=lambda x: x[0], reverse=True)
    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0], video_url[1]))

    return video_urls
