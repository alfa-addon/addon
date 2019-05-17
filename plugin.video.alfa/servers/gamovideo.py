# -*- coding: utf-8 -*-

import re
import random
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

ver = random.randint(55, 68)
if ver == 62: ver = 70
#headers = {"User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0"}
USERAGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:%s.0) Gecko/20100101 Firefox/%s.0" % (ver, ver)

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    #data = httptools.downloadpage(page_url, headers=headers, cookies=False).data
    data = httptools.downloadpage(page_url, headers={"User-Agent": USERAGENT}).data

    if "File was deleted" in data or "Not Found" in data or "File was locked by administrator" in data:
        return False, "[Gamovideo] El archivo no existe o ha sido borrado"
    if "Video is processing now" in data:
        return False, "[Gamovideo] El video está procesándose en estos momentos. Inténtelo mas tarde."
    if "File is awaiting for moderation" in data:
        return False, "[Gamovideo] El video está esperando por moderación."
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    #data = httptools.downloadpage(page_url, headers=headers, cookies=False).data
    headers = {"Host": "gamovideo.com",
               "User-Agent": USERAGENT,
               "Cookie": "gyns=1; gail=1; sugamun=1; gam=1; gew=1; cpl=1; col=1; gqm=1; luw=1; popundr=1; rtn=1;",
               "Referer": page_url.replace("embed-","")}
    data = httptools.downloadpage(page_url, headers=headers).data
    packer = scrapertools.find_single_match(data,
                                            "<script type='text/javascript'>(eval.function.p,a,c,k,e,d..*?)</script>")
    if packer != "":
        data = jsunpack.unpack(packer)

    data = re.sub(r'\n|\t|\s+', '', data)
    host = scrapertools.find_single_match(data, '\[\{image:"(http://[^/]+/)')
    mediaurl = scrapertools.find_single_match(data, ',\{file:"([^"]+)"')
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

