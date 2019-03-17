# -*- coding: utf-8 -*-
# by DrZ3r0

import urllib

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    return True, ""
    data = httptools.downloadpage(page_url).data
    if "File was deleted" in data or "Page Cannot Be Found" in data:
        return False, config.get_localized_string(70449) % "Akstream"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info(" url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data.replace('https','http')

    vres = scrapertools.find_multiple_matches(data, 'nowrap[^>]+>([^,]+)')
    data_pack = scrapertools.find_single_match(data, "(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)

    # URL
    matches = scrapertools.find_multiple_matches(data, '(http.*?\.mp4)')
    _headers = urllib.urlencode(httptools.default_headers)

    i = 0
    for media_url in matches:
        # URL del vídeo
        video_urls.append([vres[i] + " mp4 [Akstream] ", media_url + '|' + _headers])
        i = i + 1

    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0], video_url[1]))

    return video_urls
