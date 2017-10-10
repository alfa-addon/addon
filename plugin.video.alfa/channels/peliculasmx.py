# -*- coding: utf-8 -*-

import re
import urlparse

from core import scrapertools
from core import httptools
from core import tmdb
from core.item import Item

from platformcode import logger



def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(
        Item(channel=item.channel, title="Últimas añadidas", action="peliculas", url="http://www.peliculasmx.net/"))
    itemlist.append(
        Item(channel=item.channel, title="Últimas por género", action="generos", url="http://www.peliculasmx.net/"))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url="http://www.peliculasmx.net/"))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    logger.debug(data)
    # <li class="cat-item cat-item-3"><a href="http://peliculasmx.net/category/accion/" >Accion</a> <span>246</span>
    patron = '<li class="cat-item cat-item-.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '>([^<]+).*?'
    patron += '<span>([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    logger.debug(matches)
    for match in matches:
        scrapedurl = urlparse.urljoin("", match[0])
        scrapedtitle = match[1].strip() + ' [' + match[2] + ']'

        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl, folder=True))

    itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return itemlist


def peliculas(item):
    logger.info()
    extra = item.extra
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    patron = '<div id="mt-.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="tt">([^<]+).*?'
    patron += '<span class="year">(\d{4})</span>.*?'
    patron += '<span class="calidad2">([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, quality in matches:
        url =scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, contentTitle=title, url=url,
                 thumbnail=thumbnail, quality=quality, infoLabels={'year':year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, 'class="nextpostslink" rel="next" href="(.*?)">')

    if next_page:
        scrapedtitle = "!Pagina Siguiente ->"
        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=next_page, folder=True))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "+")
    try:
        # Series
        item.url = "http://www.peliculasmx.net/?s=%s" % texto
        itemlist.extend(peliculas(item))
        itemlist = sorted(itemlist, key=lambda Item: Item.title)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
