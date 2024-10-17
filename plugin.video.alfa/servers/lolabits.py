# -*- coding: utf-8 -*-
from core import httptools
from platformcode import logger
from bs4 import BeautifulSoup


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    logger.debug(data)
    if "404 - No se encontró" in data or 'La pagina que buscas no existe' in data:
        return False, "[lolabits] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    url  = soup.find('div', id='download-wrapper').a['href']
    video_urls.append(["[lolabits] mkv", url])
    return video_urls
