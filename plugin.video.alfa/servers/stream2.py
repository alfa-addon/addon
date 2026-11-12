# -*- coding: utf-8 -*-
from core import urlparse as alfa_urlparse
import re
from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url= httptools.downloadpage(page_url).url
    url= url.replace("/x", "/getlink-")
    url = alfa_urlparse.build_url(alfa_urlparse.append_path_suffix(url, '.dll'))
    logger.debug(url)
    url = httptools.downloadpage(url, headers={"referer": url}, follow_redirects=False).headers["location"]
    video_urls.append(["[streamz]", url])
    return video_urls

