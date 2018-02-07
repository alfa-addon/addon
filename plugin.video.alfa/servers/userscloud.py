# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    response = httptools.downloadpage(page_url)

    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[Userscloud] El fichero no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    unpacked = ""
    data = httptools.downloadpage(page_url).data
    packed = scrapertools.find_single_match(data, "function\(p,a,c,k.*?</script>")
    if packed:
        unpacked = jsunpack.unpack(packed)
    media_url = scrapertools.find_single_match(unpacked, 'src"value="([^"]+)')
    if not media_url:
        id_ = page_url.rsplit("/", 1)[1]
        rand = scrapertools.find_single_match(data, 'name="rand" value="([^"]+)"')
        post = "op=download2&id=%s&rand=%s&referer=%s&method_free=&method_premium=" % (id_, rand, page_url)
        data = httptools.downloadpage(page_url, post).data
        media_url = scrapertools.find_single_match(data, '<div id="dl_link".*?<a href="([^"]+)"')

    ext = scrapertools.get_filename_from_url(media_url)[-4:]
    video_urls.append(["%s [userscloud]" % ext, media_url])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
