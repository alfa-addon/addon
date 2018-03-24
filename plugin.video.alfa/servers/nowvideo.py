# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    url = page_url.replace("http://www.nowvideo.sx/video/", "http://embed.nowvideo.sx/embed/?v=")
    data = httptools.downloadpage(url).data
    if "The file is being converted" in data or "Please try again later" in data:
        return False, "El fichero está en proceso"
    elif "no longer exists" in data:
        return False, "El fichero ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    if premium:
        login_url = "http://www.nowvideo.eu/login.php"
        data = httptools.downloadpage(login_url).data
        login_url = "http://www.nowvideo.eu/login.php?return="
        post = "user=" + user + "&pass=" + password + "&register=Login"
        headers = {"Referer": "http://www.nowvideo.eu/login.php"}
        data = httptools.downloadpage(login_url, post, headers=headers).data
        data = httptools.downloadpage(page_url).data
        flashvar_file = scrapertools.get_match(data, 'flashvars.file="([^"]+)"')
        flashvar_filekey = scrapertools.get_match(data, 'flashvars.filekey=([^;]+);')
        flashvar_filekey = scrapertools.get_match(data, 'var ' + flashvar_filekey + '="([^"]+)"')
        flashvar_user = scrapertools.get_match(data, 'flashvars.user="([^"]+)"')
        flashvar_key = scrapertools.get_match(data, 'flashvars.key="([^"]+)"')
        flashvar_type = scrapertools.get_match(data, 'flashvars.type="([^"]+)"')
        url = "http://www.nowvideo.eu/api/player.api.php?user=" + flashvar_user + "&file=" + flashvar_file + "&pass=" + flashvar_key + "&cid=1&cid2=undefined&key=" + flashvar_filekey.replace(
            ".", "%2E").replace("-", "%2D") + "&cid3=undefined"
        data = httptools.downloadpage(url).data
        location = scrapertools.get_match(data, 'url=([^\&]+)&')
        location = location + "?client=FLASH"
        video_urls.append([scrapertools.get_filename_from_url(location)[-4:] + " [premium][nowvideo]", location])
    else:
        url = page_url.replace("http://www.nowvideo.sx/video/", "http://embed.nowvideo.sx/embed/?v=")
        data = httptools.downloadpage(url).data
        videourls = scrapertools.find_multiple_matches(data, 'src\s*:\s*[\'"]([^\'"]+)[\'"]')
        if not videourls:
            videourls = scrapertools.find_multiple_matches(data, '<source src=[\'"]([^\'"]+)[\'"]')
        for videourl in videourls:
            if videourl.endswith(".mpd"):
                id = scrapertools.find_single_match(videourl, '/dash/(.*?)/')
                videourl = "http://www.nowvideo.sx/download.php%3Ffile=mm" + "%s.mp4" % id
            videourl = re.sub(r'/dl(\d)*/', '/dl/', videourl)
            ext = scrapertools.get_filename_from_url(videourl)[-4:]
            videourl = videourl.replace("%3F", "?") + \
                       "|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
            video_urls.append([ext + " [nowvideo]", videourl])
    return video_urls
