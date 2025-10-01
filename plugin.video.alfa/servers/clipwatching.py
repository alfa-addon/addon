# -*- coding: utf-8 -*-

import re
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config
from core import urlparse


def test_video_exists(page_url):
    logger.error("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "File Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70292) % "ClipWatching"
    if "Video is processing now." in data:
        return False, "Intentelo más tarde: Video procesándose"
    return True, ""

def get_video_url(page_url, user="", password="", video_password=""):
    logger.error("(page_url='%s')" % page_url)
    video_urls = []
    multires = False
    videos = ''
    try:
        packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
        unpacked = jsunpack.unpack(packed)
        
    except:
        unpacked = scrapertools.find_single_match(data,"window.hola_player.*")
    
    host = httptools.obtain_domain(page_url, scheme=True)
    headers = httptools.default_headers.copy()
    headers = "|{0}&Referer={1}/&Origin={1}".format(urlparse.urlencode(headers), host)
    
    if scrapertools.find_single_match(unpacked, 'file:".*?(http[^"]+)"'): 
        m3u = scrapertools.find_single_match(unpacked, 'file:".*?(http[^"]+)"')
        m3u=m3u+headers
        
        subtitles = ''
        vttreg = re.compile('(\[[^\]]+\])(https.*?\.vtt)')
        subs = vttreg.findall(unpacked)
        if subs:
            for sub in subs:
                subtitles += sub[1] + "\n"
        
        video_urls.append(["[clipwatching] .m3u8", m3u, 0, subtitles])
    
    return video_urls
