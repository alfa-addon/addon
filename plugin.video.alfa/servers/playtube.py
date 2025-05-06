# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector playtube By Alfa development Group
# --------------------------------------------------------
import re
import codecs
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    # if "https://vtube.network/embed-" in page_url:
        # page_url = page_url.replace("https://vtube.network/embed-", "https://vtbe.to/")
    # server = scrapertools.find_single_match(page_url, '//(?:www.|es.|)([A-z0-9-]+).(?:to|ws|com)')
    data = httptools.downloadpage(page_url)
    if data.code == 404 or data.code == 504 or "File is no longer available" in data.data or "There is nothing here" in data.data or "Can't create video code" in data.data:
        return False, "[%s] El archivo no existe o ha sido borrado" %server
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    pack = scrapertools.find_single_match(data.data, 'p,a,c,k,e,d.*?</script>')
    unpacked = jsunpack.unpack(pack)
    logger.debug(unpacked)
    m3u8_source =""
    m3u8_source = scrapertools.find_single_match(unpacked, 'src="([^"]+)"')# + "|referer=%s" %(page_url)
    if not m3u8_source:
        m3u8_source = scrapertools.find_single_match(unpacked, '(?:file|src):"([^"]+)') #+ "|referer=%s" %(page_url)
    if "master.m3u8" in m3u8_source:
        datos = httptools.downloadpage(m3u8_source).data
        if isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                url =urlparse.urljoin(m3u8_source,url)
                video_urls.append(['[%s] %s' %(server, quality), url])
    else:
        video_urls.append(['[%s]' %server, m3u8_source] )
    return video_urls