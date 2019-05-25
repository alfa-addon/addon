# -*- coding: utf-8 -*-

import re
import random
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url, headers=headers).data

    page_url = page_url.replace("embed-","").replace(".html", "")

    data = httptools.downloadpage(page_url, headers=headers).data
    global DATA
    DATA = data

    if "File was deleted" in data or ("Not Found"  in data and not "|mp4|" in data) or "File was locked by administrator" in data:
        return False, "[Gamovideo] El archivo no existe o ha sido borrado"
    if "Video is processing now" in data:
        return False, "[Gamovideo] El video está procesándose en estos momentos. Inténtelo mas tarde."
    if "File is awaiting for moderation" in data:
        return False, "[Gamovideo] El video está esperando por moderación."

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url, headers=headers).data

    packer = scrapertools.find_single_match(data,
                                            "<script type='text/javascript'>(eval.function.p,a,c,k,e,d..*?)</script>")
    if packer != "":
        try:
            data = jsunpack.unpack(packer)
        except:
            pass
    else:
        original = data
        n = 0
        referer = page_url.replace("embed-","").replace(".html", "")
        headers.update({"Referer": referer})
        logger.debug("data-1 %s" % data)
        data = ""
        while n < 3 and not data:
            
            data1 = httptools.downloadpage(page_url, headers=headers).data
            check_c, data = get_gcookie(data1, True)
            if check_c == False:
                logger.error("Error get gcookie(%d):%s" % (n, data1))
            n += 1


    data = re.sub(r'\n|\t|\s+', '', data)
    host = scrapertools.find_single_match(data, r'\[\{image:"(http://[^/]+/)')
    mediaurl = scrapertools.find_single_match(data, r',\{file:"([^"]+)"')
    if not mediaurl.startswith(host):
        mediaurl = host + mediaurl

    rtmp_url = scrapertools.find_single_match(data, 'file:"(rtmp[^"]+)"')
    playpath = scrapertools.find_single_match(rtmp_url, 'mp4:.*$')
    rtmp_url = rtmp_url.split(playpath)[
                   0] + " playpath=" + playpath + " swfUrl=http://gamovideo.com/player61/jwplayer.flash.swf"

    video_urls = []
    video_urls.append(["RTMP [gamovideo]", rtmp_url])
    video_urls.append([scrapertools.get_filename_from_url(mediaurl)[-4:] + " [gamovideo]", mediaurl])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

def get_gcookie(data, realcheck=False):
    packer = scrapertools.find_single_match(data,
                                            "<script type='text/javascript'>(eval.function.p,a,c,k,e,d..*?)</script>")
    if packer != "" and realcheck:
        try:
            data = jsunpack.unpack(packer)
            return True, data
        except:
            pass
    patron = '\("\d","(\d)",\d\).*?\'(\w+)'
    scraper = scrapertools.find_single_match(data,patron)
    if scraper:
        gcookie = "%s=%s;" % (scraper[1], scraper[0])
        try:
            old_gcookie = headers['Cookie']
            if gcookie != old_gcookie:
                gcookie = old_gcookie+' '+gcookie
        except:
            pass
        headers.update({"Cookie": gcookie})
        return True, ""
    else:
        return False, ""