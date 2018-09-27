# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Video not found..." in data:
        return False, config.get_localized_string(70292) % "Thevid"
    if "Video removed for inactivity..." in data:
        return False, "[Thevid] El video ha sido removido por inactividad"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    packed = scrapertools.find_multiple_matches(data, "(?s)<script>\s*eval(.*?)\s*</script>")
    for pack in packed:
        unpacked = jsunpack.unpack(pack)
        if "file" in unpacked:
            videos = scrapertools.find_multiple_matches(unpacked, 'file.="(//[^"]+)')
    video_urls = []
    for video in videos:
        video = "https:" + video
        video_urls.append(["mp4 [Thevid]", video])
    logger.info("Url: %s" % videos)
    return video_urls
