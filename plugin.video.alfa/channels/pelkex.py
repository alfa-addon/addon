# -*- coding: utf-8 -*-
# -*- Channel Pelkex -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://pelkex.net/'

IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload', 'streamango', 'fastplay', 'okru', 'rapidvideo']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + '?s=', pages=2,
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section",
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url=host + '?s=', pages=3,
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    i = 1
    while i <= item.pages:
        try:
            data = get_source(item.url)
        except:
            break
        patron = '<div class="card-image"><a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" />.*?'
        patron += '</h3><p>([^<]+)</p>.*?</i>(\d{4})</li>'

        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, scrapedtitle, plot, year in matches:
            url = scrapedurl
            scrapedtitle = scrapedtitle
            thumbnail = scrapedthumbnail
            new_item = Item(channel=item.channel, title=scrapedtitle, url=url, action='findvideos',
                            thumbnail=thumbnail, plot=plot, infoLabels={'year':year})

            new_item.contentTitle=scrapedtitle
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        # Paginacion

        if itemlist != []:

            next_page = scrapertools.find_single_match(data, "href='#'>\d+</a></li><li class='page-item'>"
                                                             "<a class='page-link' href='([^']+)'>")
            if next_page != '' and i == item.pages:
                itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>', url=next_page,
                                     pages=item.pages))
            else:
                item.url=next_page
        i += 1

    return itemlist



def section(item):
    logger.info()

    itemlist = []
    data=get_source(host)
    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, 'tabindex="0">Generos<.*?</ul>')
    elif 'Años' in item.title:
        data = scrapertools.find_single_match(data, 'tabindex="0">Año<.*?</ul>')

    patron = 'href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='list_all', pages=3))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<div id="[^"]+" class="tab.*?"><(?:iframe|IFRAME).*?(?:src|SRC)="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        if 'http' not in scrapedurl:
            url = 'http:'+scrapedurl
        else:
            url = scrapedurl

        itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language=IDIOMAS['Latino'],
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + '?s='
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        item.pages=3
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

