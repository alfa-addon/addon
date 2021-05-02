# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidtodo By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack

id_server = "vidtodo"
response = ""
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global response
    response = httptools.downloadpage(page_url, add_referer=True)

    if not response.sucess or "Not Found" in response.data:
        return False, "[%s] El fichero no existe o ha sido borrado" %id_server
    if not response.sucess or "Video is processing now." in response.data:
        return False, "[%s] El video se está procesando." %id_server
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = response.data
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)\s*</script>")
    unpacked = jsunpack.unpack(packed_data)
    matches = scrapertools.find_multiple_matches(unpacked, 'file:"([^"]+)",label:"([^"]+)"')
    for media_url, res in matches:
        if media_url.endswith(".mp4"):
            video_urls.append(["[%s][%s]" % (".mp4", res), media_url])
        if media_url.endswith(".m3u8"):
            video_urls.append(["M3U8 [%s][%s]" % (".m3u8", res), media_url])
        if media_url.endswith(".smil"):
            smil_data = httptools.downloadpage(media_url).data
            rtmp = scrapertools.find_single_match(smil_data, 'base="([^"]+)"')
            playpaths = scrapertools.find_single_match(smil_data, 'src="([^"]+)" height="(\d+)"')
            mp4 = "http:" + scrapertools.find_single_match(rtmp, '(//[^:]+):') + "/%s/" + \
                  scrapertools.find_single_match(data, '"Watch video ([^"]+")').replace(' ', '.') + ".mp4"
            for playpath, inf in playpaths:
                h = scrapertools.find_single_match(playpath, 'h=([a-z0-9]+)')
                video_urls.append([".mp4 [%s] %s" % (id_server, inf), mp4 % h])
                video_urls.append(["RTMP [%s] %s" % (id_server, inf), "%s playpath=%s" % (rtmp, playpath)])
    for video_url in video_urls:
        logger.info("video_url: %s - %s" % (video_url[0], video_url[1]))
    return video_urls
