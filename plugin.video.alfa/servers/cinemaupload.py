# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Cinemaupload By Alfa development Group
# --------------------------------------------------------
import os
import re
import json
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data

    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)

    url = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers.get("location", "")
    data = httptools.downloadpage(url)
    if data.code == 404:
        return False, "[CinemaUpload] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url1=" + page_url)
    if '|' in page_url:
        page_url, referer = page_url.split("|", 1)
    video_urls = list()
    patron = 'file: "([^"]+)",'
    matches = scrapertools.find_multiple_matches(data.data, patron)
    for url in matches:
        url += "|verifypeer=false&Referer=%s" %page_url
        if ".mp4" in url:
            video_urls.append(['.mp4 [CinemaUpload]', url])
        else:
            video_urls.append(['.mpd [CinemaUpload]', url,0,"", "mpd"])
    return video_urls
