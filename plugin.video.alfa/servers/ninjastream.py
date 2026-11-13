# -*- coding: utf-8 -*-
from core import urlparse as alfa_urlparse
import re
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info()
    data = httptools.downloadpage(page_url).data
    if "not found" in data:
        return False, "[ninjastream] El video ha sido borrado o no existe"
    global data
    return True, ""




def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    stream = scrapertools.find_single_match(data, 'v-bind:stream="([^"]+)"')
    stream = stream.replace('&quot;', '"')
    host = scrapertools.find_single_match(stream, '"host":"([^"]+)"')
    hash = scrapertools.find_single_match(stream, '"hash":"([^"]+)"')
    host = host.decode('unicode-escape').encode('utf8')
    host = decod2(host)
    url = alfa_urlparse.build_url(host, u'{}/index.m3u8'.format(hash))
    data = httptools.downloadpage(url).data
    patron  = '([0-9_]+p.m3u8)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality in matches:
        url = alfa_urlparse.build_url(host, u'{}/{}'.format(hash, quality))
        url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}'.format(page_url)})
        quality = scrapertools.find_single_match(quality, '(\d+p).m3u8')
        video_urls.append(["[ninjastream] %s" %quality, url])
    return video_urls


def decod2(host):
    s = ''
    for n in range(len(host)):
        s += chr(ord(host[n]) ^ ord('2'))
    return s

