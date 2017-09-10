# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(page_url).data)

    match = scrapertools.find_single_match(data, "<script type='text/javascript'>(.*?)</script>")
    data = jsunpack.unpack(match)
    data = data.replace("\\'", "'")

    media_url = scrapertools.find_single_match(data, '{type:"video/mp4",src:"([^"]+)"}')
    logger.info("media_url=" + media_url)

    video_urls = list()
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mp4upload]", media_url])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
