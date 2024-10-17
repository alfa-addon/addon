# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Fastream By Alfa Development Group
# --------------------------------------------------------

import sys
from core import httptools, scrapertools
from platformcode import config, logger
from lib import jsunpack

PY3 = sys.version_info >= (3,)

kwargs = {
    "set_tls": True,
    "set_tls_min": True,
    "retries_cloudflare": 0,
    "ignore_response_code": True,
    "cf_assistant": False,
}

data = ""


def test_video_exists(page_url):
    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)

    global data
    data = httptools.downloadpage(page_url, **kwargs).data
    if "File is no longer available as it expired or has been deleted" in data:
        return False, (config.get_localized_string(70449) % "fastream")
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)
    global data

    packed = scrapertools.find_single_match(
        data, "text/javascript'>(eval.*?)\s*</script>"
    )
    unpacked = jsunpack.unpack(packed)
    data = scrapertools.find_single_match(unpacked, "(?is)sources.+?\[(.+?)\]")

    # servertools.parse_hls se encarga de mostrar las calidades
    m3u = scrapertools.find_single_match(data, 'file:"([^"]+)"')
    video_urls.append(["[fastream] .m3u8", m3u])
    
    return video_urls
