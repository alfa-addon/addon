# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Megaup By Alfa development Group
# --------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    response = httptools.downloadpage(page_url)
    data = response.data
    
    msg_error = scrapertools.find_single_match(data, "<li class='no-side-margin'>([^<]+)</li>")
    
    if response.code == 404 or "no longer available!" in msg_error or "File not found" in data:
        return False, "[Megaup] El fichero no existe o ha sido borrado"
    elif msg_error:
        return False, "[Megaup] %s" % msg_error
    return True, ""

# https://megaup.net/3bb40e9c19442d749f4528b79a5a649e/Furia.Asesina.2024.1080P.Latino.mkv

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    import time
    logger.info("url=" + page_url)
    video_urls = []
    
    global data
    
    media_url = ""
    url = scrapertools.find_single_match(data,"<a class='btn btn--primary' href='([^<]+)'")
    url += "|Referer=%s" % url
    if url:
        time.sleep(5.5)
        data_url = httptools.downloadpage(url, follow_redirects=False)
        media_url = data_url.headers.get('location', '')
    # response = httptools.downloadpage(url)
    # logger.debug(response.data)
    from lib import alfa_assistant
    response = alfa_assistant.get_source_by_page_finished(url, 5, closeAfter=True, debug=True)
    # data = response.data
    # logger.debug(response['htmlSources']['url'])
    ext = scrapertools.find_single_match(data, '<div class="heading-1">([^<]+)')[-4:]
    url = scrapertools.find_single_match(data, "' href='([^']+)'>download now")
    
    
    if media_url:
        video_urls.append(["%s [Megaup]" % ext, media_url])

    return video_urls
