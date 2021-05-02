# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Oprem By Alfa development Group
# --------------------------------------------------------

import os
from core import httptools
from core import scrapertools
from platformcode import logger, config
from lib import servop


def test_video_exists(page_url):

    logger.info("(page_url='%s')" % page_url)
    global data

    ref = page_url.split('//', 1)
    data = httptools.downloadpage(page_url, headers={"referer": ref[0] + "//" + ref[1]})

    if data.code == 404:
        return False, "[oprem] El archivo no existe o ha sido borrado"
    data = data.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = list()
    if "const source = '" in data:
        url = scrapertools.find_single_match(data, "const source = '([^']+)")
        v_type = "hls"
    else:
        url, v_type = scrapertools.find_single_match(data, '"file": "([^"]+)",\s+"type": "([^"]+)"')
    headers = {"referer": page_url}

    if v_type == "mp4":
        url = httptools.downloadpage(url, headers=headers, follow_redirects=False, stream=True).headers["location"]
        page_url = "%s|Referer=%s&User-Agent=%s" % (url, page_url, httptools.get_user_agent())

    elif v_type == "hls":

        hls_data = httptools.downloadpage(url, headers=headers).data
        base_url = scrapertools.find_single_match(hls_data, "(https?://[^/]+)")
        hls_data = hls_data.replace(base_url, 'http://localhost:8781')
        m3u8 = os.path.join(config.get_data_path(), "op_master.m3u8")
        outfile = open(m3u8, 'wb')
        outfile.write(hls_data)
        outfile.close()
        page_url = m3u8
        v_type = "m3u8"
        servop.start(base_url)
    else:
        return video_urls

    video_urls = [["%s [Oprem]" % v_type, page_url]]

    return video_urls
