# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Page not found" in data or "File was deleted" in data:
        return False, "[vidoza] El archivo no existe o ha sido borrado"
    elif "processing" in data:
        return False, "[vidoza] El vídeo se está procesando"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    video_urls = []

    s = scrapertools.find_single_match(data, 'sourcesCode\s*:\s*(\[\{.*?\}\])')
    s = s.replace('src:', '"src":').replace('type:', '"type":').replace('label:', '"label":').replace('res:', '"res":')
    try:
        data = json.loads(str(s))
        for enlace in data:
            if 'src' in enlace:
                tit = ''
                if 'label' in enlace: tit += '[%s]' % enlace['label']
                if 'res' in enlace: tit += '[%s]' % enlace['res']
                if tit == '' and 'type' in enlace: tit = enlace['type']
                if tit == '': tit = '.mp4'
                
                video_urls.append(["%s [vidoza]" % tit, enlace['src']])
    except:
        logger.debug('No se detecta json %s' % s)
        pass

    video_urls.reverse()

    return video_urls
