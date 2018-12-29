# -*- coding: utf-8 -*-
# -*- Channel Repelis.live -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from channels import filtertools
from channels import autoplay

IDIOMAS = {'Latino': 'LAT', 'Castellano':'CAST', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload', 'streamango', 'rapidvideo', 'netutv']

host = "http://repelis.live/"

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(
        Item(channel=item.channel,
             title="Ultimas",
             action="list_all",
             url=host,
             thumbnail=get_thumb("last", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Castellano",
             action="list_all",
             url=host+'pelis-castellano/',
             thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Latino",
             action="list_all",
             url=host+'pelis-latino/',
             thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="VOSE",
             action="list_all",
             url=host+'pelis-subtitulado/',
             thumbnail=get_thumb("vose", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Generos",
             action="categories",
             url=host,
             thumbnail=get_thumb('genres', auto=True)
             ))

    itemlist.append(
        Item(channel=item.channel,
             title="Por Año",
             action="categories",
             url=host,
             thumbnail=get_thumb('year', auto=True)
             ))

    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host + '?s=',
             thumbnail=get_thumb("search", auto=True)
             ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def categories(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    if item.title != 'Generos':
        patron = '<option value="([^"]+)">([^<]+)</option>'
    else:
        data = scrapertools.find_single_match(data, '</span>Categories</h3><ul>(.*?)</ul>')
        patron = '<a href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=title,
                             url=url
                             ))
    return itemlist





def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    if item.title == 'Buscar':
        pattern = '<div class="row"> <a href="([^"]+)" title="([^\(]+)\(.*?">.*?<img src="([^"]+)".*?'
        pattern += '<p class="main-info-list">Pelicula del (\d{4})'
    else:
        pattern = '<div class="col-mt-5 postsh">.?<div class="poster-media-card"> <a href="([^"]+)" '
        pattern += 'title="([^\(]+)\(.*?">.*?"anio".*?>(\d{4}).*?src="([^"]+)"'

    matches = scrapertools.find_multiple_matches(data, pattern)

    for url, title, year, thumb in matches:

        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        action='findvideos',
                        contentTitle=title,
                        thumbnail=thumb,
                        infoLabels = {'year': year}
                        )

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if next_page != '':
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=next_page,
                             ))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    trailer = ''
    data = get_source(item.url)
    patron = '<a href="#embed\d+".*?data-src="([^"]+)".*?"tab">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, language in matches:
        url = url.replace('&#038;','&')
        data = httptools.downloadpage(url, follow_redirects=False, headers={'Referer':item.url}, only_headers=True)
        url = data.headers['location']

        if config.get_setting('unify'):
            title = ''
        else:
            title = ' [%s]' % language

        if 'youtube' in url:
            trailer = Item(channel=item.channel, title='Trailer', url=url, action='play', server='youtube')
        else:
            itemlist.append(Item(channel=item.channel,
                                 title='%s'+title,
                                 url=url,
                                 action='play',
                                 language=IDIOMAS[language],
                                 infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    if trailer != '':
        itemlist.append(trailer)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)


    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle
                             ))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    try:
        if texto != '':
            item.url += texto
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host
        elif category == 'infantiles':
            item.url = host + 'category/animacion'
        elif category == 'terror':
            item.url = host + 'category/terror'
        itemlist = list_all(item)

        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
