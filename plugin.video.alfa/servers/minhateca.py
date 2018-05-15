# -*- coding: utf-8 -*-

import urllib

from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    return True, ""

def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    _rvt = scrapertools.find_single_match(data, '__RequestVerificationToken.*?value="([^"]+)"')
    _fileid = scrapertools.find_single_match(data, 'data-fileid="([^"]+)"')
    post = {'fileId': _fileid, '__RequestVerificationToken': _rvt}
    post = urllib.urlencode(post)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    url1 = "http://minhateca.com.br/action/License/Download"
    data = httptools.downloadpage(url1, post = post, headers = headers).data
    dict_data = jsontools.load(data)
    videourl = dict_data["redirectUrl"] + "|Referer=%s" %page_url
    video_urls.append([".MP4 [minhateca]", videourl])
    return video_urls
