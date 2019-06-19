# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector jetload By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools, jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, "[jetload] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    subtitles = ""
    data = httptools.downloadpage(page_url).data
    srv = scrapertools.find_single_match(data, 'id="srv" value="([^"]+)"')
    srv_id = scrapertools.find_single_match(data, 'id="srv_id" value="([^"]+)"')
    file_name = scrapertools.find_single_match(data, 'file_name" value="([^"]+)"')
    file_id = scrapertools.find_single_match(data, 'file_id" value="([^"]+)"')
    archive = scrapertools.find_single_match(data, 'archive" value="([^"]+)"')
    try:
        data_sub = httptools.downloadpage("https://jetload.net/api/get/subtitles/%s" % file_id).data
        subtitles = "https://jetload.net/tmp/%s" % jsontools.load(data_sub)[0]["sub_file"]
    except:
        pass
    if srv_id:
        post = jsontools.dump({"file_name":file_name+".mp4", "srv":srv_id})
        data = httptools.downloadpage("https://jetload.net/api/download", post=post, headers={"Content-Type":"application/json;charset=UTF-8"}).data
        media_url = data
        video_urls.append([".mp4 [jetload]", media_url, 0, subtitles ])
    else:
        m3u8 = srv + "/v2/schema/%s/master.m3u8" %file_name
        if archive == '1':
            m3u8 = srv + "/v2/schema/archive/%s/master.m3u8" %file_name
        data = httptools.downloadpage(m3u8).data
        data = re.sub(r"\n|\r|\t|\s{2}", "", data)
        matches = scrapertools.find_multiple_matches(data, r'RESOLUTION=\d+x(\d+)(\w+).m3u8')
        for res, uri in matches:
            res = res+"p"
            media_url = m3u8.replace("master", uri)
            video_urls.append([".m3u8 (%s) [jetload]" % res, media_url, 0, subtitles ])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
