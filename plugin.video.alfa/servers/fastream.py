# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Fastream By Alfa Development Group
# --------------------------------------------------------
import re
from core import httptools, servertools, scrapertools
from platformcode import config, logger

data = ''

def resolve_patterns(page_url):
    # Recorre los patrones
    server_parameters = servertools.get_server_parameters("fastream")
    patterns = server_parameters.get("find_videos", {}).get("patterns")
    for pattern in patterns:
        for match in re.compile(pattern["pattern"], re.DOTALL).finditer(page_url):
            url = pattern["url"]
            for x in range(len(match.groups())):
                url = url.replace("\\{}".format(x + 1), match.groups()[x])
            page_url = url
    return page_url


def test_video_exists(page_url):
    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)

    logger.info("(page_url='{}')".format(page_url))
    page_url = resolve_patterns(page_url)
    logger.info("pre_resolved_url={}".format(page_url))

    if 'referer' in locals():
        page_url += referer

    global data
    data = httptools.downloadpage(page_url).data

    if 'File is no longer available as it expired or has been deleted' in data:
        return False, (config.get_localized_string(70449) % "fastream")
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url1={}".format(page_url))
    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)
    global data

    if not data:
        page_url = resolve_patterns(page_url)
        logger.info("pre_resolved_url={}".format(page_url))
        data = httptools.downloadpage(page_url).data
    data = scrapertools.find_single_match(data, "(?is)var player =.+?sources.+?\[(.+?)\]")

    video_urls = []
    pattern = "(?is)src: [\"'](.+?)[\"']"
    matches = scrapertools.find_multiple_matches(data, pattern)
    for url in matches:
        if 'referer' in locals():
            url += "|Referer={}".format(referer)
        logger.info(url)
        video_urls.append(['.m3u8 [fastream]', url])
    return video_urls
