# s-*- coding: utf-8 -*-
from core import httptools
from platformcode import config, logger
import re

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data_json
    if "https://www.youtube.com/watch?v=" not in page_url:
        return False, "Youtube - Invalid URL"
    page_url = page_url.replace("https://www.youtube.com/watch?v=", "")
    video_match = re.match(r"^([0-9A-Za-z_-]{11})", page_url)
    if not video_match:
        return False, "Youtube - Invalid Video ID"
    video_id = video_match.group(1)
    page_url = "https://inv.perditum.com/api/v1/videos/%s" % video_id
    data_json = httptools.downloadpage(page_url).json
    if not data_json or data_json.get("error", ""):
        return False, config.get_localized_string(70449) % "Youtube"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    global data_json    
    video_urls = []
    if data_json:
        videodash = data_json.get("dashUrl", "")
        if videodash:
            video_urls.append( ["Youtube", videodash, 0, "", "mpd"] )
    return video_urls