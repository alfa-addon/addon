# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger



def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global response

    response = httptools.downloadpage(page_url)
    if response.json.get("error", ""):
        return False, "[Dailymotion] El archivo no existe o ha sido borrado"
    if response.code == 404:
        return False, "[Dailymotion] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = response.json
    #subtitle = scrapertools.find_single_match(data, '"subtitles":.*?"es":.*?urls":\["([^"]+)"')
    #qualities = scrapertools.find_multiple_matches(data, '"([^"]+)":(\[\{"type":".*?\}\])')
    stream_url = data['qualities']['auto'][0]['url']

    #logger.error(stream_url)
    data_m3u8 = httptools.downloadpage(stream_url).data

    patron = r'NAME="([^"]+)",PROGRESSIVE-URI="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data_m3u8, patron)

    for calidad, url in matches:
        url = httptools.get_url_headers(url, forced=True, dom='dailymotion.com')
        video_urls.append(["%sp .mp4 [dailymotion]" % calidad, url])
    return video_urls
