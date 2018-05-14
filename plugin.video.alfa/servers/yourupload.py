# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "File was deleted" in data or "File not found" in data:
        return False, "[Yourupload] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    url1 = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers.get("location", "")
    referer = {'Referer': page_url}
    url = scrapertools.find_single_match(data, '<meta property="og:video" content="([^"]+)"')
    if not url:
        if "download" in page_url:
            url = httptools.downloadpage("https:" + url1, headers=referer, follow_redirects=False, only_headers=True).headers.get("location", "")
        else:
            url = scrapertools.find_single_match(data, "file:\s*'([^']+)'")
    if url:
        if "vidcache" not in url:
            url = "https://www.yourupload.com%s" % url
            location = httptools.downloadpage(url, headers=referer, follow_redirects=False, only_headers=True)
            media_url = location.headers["location"].replace("?start=0", "").replace("https", "http")
            ext = media_url[-4:]
            media_url += "|Referer=%s" % url
        else:
            ext = url[-4:]
            media_url = url +"|Referer=%s" % page_url
        video_urls.append([ext + " [yourupload]", media_url])
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))
    return video_urls
