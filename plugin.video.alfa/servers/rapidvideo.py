# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    try:
        response = httptools.downloadpage(page_url)
    except:
        pass

    if not response.data or "urlopen error [Errno 1]" in str(response.code):
        from platformcode import config
        if config.is_xbmc():
            return False, "[Rapidvideo] Este conector solo funciona a partir de Kodi 17"
        elif config.get_platform() == "plex":
            return False, "[Rapidvideo] Este conector no funciona con tu versión de Plex, intenta actualizarla"
        elif config.get_platform() == "mediaserver":
            return False, "[Rapidvideo] Este conector requiere actualizar python a la versión 2.7.9 o superior"

    if "Object not found" in response.data:
        return False, "[Rapidvideo] El archivo no existe o ha sido borrado"
    if response.code == 500:
        return False, "[Rapidvideo] Error de servidor, inténtelo más tarde."

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron = 'https://www.rapidvideo.com/e/[^"]+'
    match = scrapertools.find_multiple_matches(data, patron)
    if match:
        for url1 in match:
           res = scrapertools.find_single_match(url1, '=(\w+)')
           data = httptools.downloadpage(url1).data
           url = scrapertools.find_single_match(data, 'source src="([^"]+)')
           ext = scrapertools.get_filename_from_url(url)[-4:]
           video_urls.append(['%s %s [rapidvideo]' % (ext, res), url])
    else:
        patron = 'data-setup.*?src="([^"]+)".*?'
        patron += 'type="([^"]+)"'
        match = scrapertools.find_multiple_matches(data, patron)
        for url, ext in match:
            video_urls.append(['%s [rapidvideo]' % (ext), url])
    return video_urls
