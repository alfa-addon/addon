# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(action="categorias", title="Categorías", url="http://dato.porn/categories_all", contentType="movie", viewmode="movie"))
    itemlist.append(item.clone(title="Buscar...", action="search", contentType="movie", viewmode="movie"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = "http://dato.porn/?k=%s&op=search" % texto.replace(" ", "+")
    return lista(item)


def lista(item):
    logger.info()
    itemlist = []

    # Descarga la pagina 
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)

    # Extrae las entradas
    patron = '<div class="videobox">\s*<a href="([^"]+)".*?url\(\'([^\']+)\'.*?<span>(.*?)<\/span><\/div><\/a>.*?class="title">(.*?)<\/a><span class="views">.*?<\/a><\/span><\/div> '
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, duration, scrapedtitle in matches:
        if "/embed-" not in scrapedurl:
            #scrapedurl = scrapedurl.replace("dato.porn/", "dato.porn/embed-") + ".html"
            scrapedurl = scrapedurl.replace("datoporn.co/", "datoporn.co/embed-") + ".html"
        if duration:
            scrapedtitle = "%s - %s" % (duration, scrapedtitle)
        scrapedtitle += ' gb'
        scrapedtitle = scrapedtitle.replace(":", "'")

        #logger.debug(scrapedurl + ' / ' + scrapedthumbnail + ' / ' + duration + ' / ' + scrapedtitle)
        itemlist.append(item.clone(action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   server="datoporn", fanart=scrapedthumbnail.replace("_t.jpg", ".jpg")))

    # Extrae la marca de siguiente página
    #next_page = scrapertools.find_single_match(data, '<a href=["|\']([^["|\']+)["|\']>Next')
    next_page = scrapertools.find_single_match(data, '<a class=["|\']page-link["|\'] href=["|\']([^["|\']+)["|\']>Next')
    if next_page and itemlist:
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    # Descarga la pagina    
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    patron = '<div class="vid_block">\s*<a href="([^"]+)".*?url\((.*?)\).*?<span>(.*?)</span>.*?<b>(.*?)</b>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, numero, scrapedtitle in matches:
        if numero:
            scrapedtitle = "%s  (%s)" % (scrapedtitle, numero)

        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail))

    return itemlist
