# -*- coding: utf-8 -*-
# -*- Server BurstCloud -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    page_url = urlparse.unquote(page_url)
    data = httptools.downloadpage(page_url)

    if data.code == 404:
        return False, "[burstcloud] El fichero no existe o ha sido borrado"
    data = data.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    base_url = "https://www.burstcloud.co/file/play-request/"
    fileId = scrapertools.find_single_match(data, 'data-file-id="([^"]+)"')
    post = {"fileId": fileId}
    v_data = httptools.downloadpage(base_url, post=post, headers={"referer": page_url}).json
    url = httptools.downloadpage(v_data["purchase"]["cdnUrl"]).url + "|referer=https://www.burstcloud.co/"
    video_urls.append(['[burstcloud] MP4', url])

    return video_urls

