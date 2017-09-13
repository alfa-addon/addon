# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(item.clone(action="lista", title="Novedades", url="http://www.pelisxporno.com/?order=date"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url="http://www.pelisxporno.com/categorias/"))
    itemlist.append(item.clone(action="search", title="Buscar", url="http://www.pelisxporno.com/?s=%s"))

    return itemlist


def search(item, texto):
    logger.info()
    item.url = item.url % texto
    return lista(item)


def lista(item):
    logger.info()
    itemlist = []

    # Descarga la pagina  
    data = httptools.downloadpage(item.url).data
    # Extrae las entradas (carpetas)
    patron = '<div class="video.".*?<a href="(.*?)" title="(.*?)">.*?<img src="(.*?)".*?\/>.*?duration.*?>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, duration in matches:
        if duration:
            scrapedtitle += "  (%s)" % duration

        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail))

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)"')
    if next_page:
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    # Descarga la pagina  
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    patron = '<li class="cat-item cat-item-.*?"><a href="(.*?)".*?>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl))

    return itemlist
